"""
Dual Browser Manager — Single browser, two tabs in one window:
  - main_page (tab 1): Stays on the target site (Appy Pie). NEVER navigates away.
  - helper_page (tab 2): Used for auxiliary tasks (Yopmail OTP, verification links).
"""
import os
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from config import HEADLESS, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, SCREENSHOT_DIR, NAVIGATION_TIMEOUT

RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "recordings")


class DualBrowser:
    def __init__(self):
        self._playwright = None

        # Single browser + single context with two tabs
        self._main_browser: Browser | None = None
        self._main_context: BrowserContext | None = None
        self.main_page: Page | None = None
        self.helper_page: Page | None = None
        self.video_path: str | None = None

    async def launch(self, record_video: bool = True):
        self._playwright = await async_playwright().start()

        # Prepare recordings dir
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        # Launch a single browser instance
        self._main_browser = await self._playwright.chromium.launch(headless=HEADLESS)

        context_opts = {
            "viewport": {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        }
        if record_video:
            context_opts["record_video_dir"] = RECORDINGS_DIR
            context_opts["record_video_size"] = {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}

        # Single context — helper tab created lazily when needed
        self._main_context = await self._main_browser.new_context(**context_opts)

        # Tab 1: Main page — stays on target site
        self.main_page = await self._main_context.new_page()
        self.main_page.set_default_timeout(NAVIGATION_TIMEOUT)

        # Helper page is NOT created here — created on first access via get_helper_page()

        print("  [dual-browser] Single browser launched with one tab")

    async def get_helper_page(self) -> Page:
        """Lazily create and return the helper tab — only opens when needed."""
        if self.helper_page is None or self.helper_page.is_closed():
            self.helper_page = await self._main_context.new_page()
            self.helper_page.set_default_timeout(NAVIGATION_TIMEOUT)
            # Bring main tab back to front after creating helper
            await self.main_page.bring_to_front()
            print("  [dual-browser] Helper tab opened (on demand)")
        return self.helper_page

    @property
    def main_context(self) -> BrowserContext:
        return self._main_context

    @property
    def helper_context(self) -> BrowserContext:
        return self._main_context

    async def main_goto(self, url: str):
        """Navigate the main browser."""
        await self.main_page.goto(url, wait_until="domcontentloaded")
        try:
            await self.main_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

    async def main_url(self) -> str:
        try:
            await self._recover_main_page()
            return self.main_page.url
        except Exception:
            return ""

    async def _recover_main_page(self):
        """If main page was closed/crashed, recover it (skip the helper tab)."""
        try:
            if self.main_page is None or self.main_page.is_closed():
                pages = [p for p in self._main_context.pages if p != self.helper_page]
                if pages:
                    self.main_page = pages[0]
                else:
                    self.main_page = await self._main_context.new_page()
                    self.main_page.set_default_timeout(NAVIGATION_TIMEOUT)
                print("  [dual-browser] Recovered main page")
        except Exception:
            pass

    async def main_screenshot(self, step: int, label: str = "") -> str:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        suffix = f"_{label}" if label else ""
        path = os.path.join(SCREENSHOT_DIR, f"step_{step:03d}{suffix}.png")
        try:
            await self._recover_main_page()
            await self.main_page.screenshot(path=path, full_page=False)
        except Exception:
            pass
        return path

    async def helper_screenshot(self, step: int, label: str = "") -> str:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        suffix = f"_{label}" if label else ""
        path = os.path.join(SCREENSHOT_DIR, f"helper_{step:03d}{suffix}.png")
        try:
            helper = await self.get_helper_page()
            await helper.screenshot(path=path, full_page=False)
        except Exception:
            pass
        return path

    async def wait_for_main_ready(self, timeout: int = 10000):
        """Wait for interactive elements to appear on main page."""
        await self._recover_main_page()
        try:
            await self.main_page.wait_for_selector(
                "input, button, form, textarea, [role='button']",
                state="visible", timeout=timeout
            )
        except Exception:
            pass
        await asyncio.sleep(1)

    async def get_main_interactive_elements(self) -> str:
        """Extract interactive elements from the main browser page."""
        await self._recover_main_page()
        await self.wait_for_main_ready()

        try:
            return await self._extract_elements()
        except Exception:
            # Page may have navigated — recover and retry once
            await asyncio.sleep(2)
            await self._recover_main_page()
            try:
                await self.main_page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(1)
            try:
                return await self._extract_elements()
            except Exception:
                return "[]"

    async def _extract_elements(self) -> str:
        return await self.main_page.evaluate("""() => {
            const selectors = [
                'a[href]', 'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="link"]', '[role="tab"]',
                '[onclick]', '[type="submit"]', 'form',
                'h1', 'h2', 'h3', 'label', '[aria-label]',
                '[contenteditable]', '.chat-input', '.message-input'
            ];
            const elements = [];
            const seen = new Set();

            for (const sel of selectors) {
                for (const el of document.querySelectorAll(sel)) {
                    if (seen.has(el)) continue;
                    seen.add(el);

                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;

                    const tag = el.tagName.toLowerCase();
                    const attrs = {};
                    for (const attr of ['id', 'name', 'type', 'href', 'placeholder',
                                         'aria-label', 'role', 'value', 'class', 'contenteditable']) {
                        if (el.getAttribute(attr)) {
                            attrs[attr] = el.getAttribute(attr).substring(0, 150);
                        }
                    }
                    const text = (el.innerText || '').substring(0, 200).trim();

                    elements.push({
                        tag, attrs, text,
                        selector: buildSelector(el),
                        bbox: {x: Math.round(rect.x), y: Math.round(rect.y),
                               w: Math.round(rect.width), h: Math.round(rect.height)}
                    });
                }
            }

            function buildSelector(el) {
                if (el.id) return '#' + CSS.escape(el.id);
                if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
                const tag = el.tagName.toLowerCase();
                const text = (el.innerText || '').trim().substring(0, 40);
                if (text && ['button', 'a'].includes(tag)) {
                    return tag + ':has-text("' + text.replace(/"/g, '\\\\"') + '")';
                }
                if (el.className && typeof el.className === 'string') {
                    const cls = el.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
                    return tag + cls;
                }
                return tag;
            }

            return JSON.stringify(elements, null, 2);
        }""")

    async def close(self) -> str | None:
        """Close browser and return the video file path."""
        video_path = None
        # Save video path before closing
        try:
            if self.main_page and self.main_page.video:
                video_path = await self.main_page.video.path()
        except Exception:
            pass

        if self._main_context:
            await self._main_context.close()
        if self._main_browser:
            await self._main_browser.close()
        if self._playwright:
            await self._playwright.stop()

        self.video_path = video_path
        return video_path
