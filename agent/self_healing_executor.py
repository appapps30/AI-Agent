"""
Self-Healing Executor — Executes actions with multiple fallback strategies.

Priority order:
1. Direct Playwright locator (CSS selector)
2. Text-based locator
3. JavaScript injection
4. Scroll + retry
"""
import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout


class SelfHealingExecutor:
    def __init__(self, page: Page):
        self.page = page

    async def execute(self, action: dict) -> dict:
        """Execute an action with self-healing fallbacks."""
        action_type = action.get("action", "done")

        try:
            if action_type == "click":
                return await self._click_with_healing(action)
            elif action_type == "fill":
                return await self._fill_with_healing(action)
            elif action_type == "select":
                return await self._select(action)
            elif action_type == "navigate":
                return await self._navigate(action)
            elif action_type == "scroll":
                return await self._scroll(action)
            elif action_type == "wait":
                return await self._wait(action)
            elif action_type == "press_enter":
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(1)
                return {"success": True, "message": "Pressed Enter"}
            elif action_type in ("done", "signup_done", "need_otp"):
                return {"success": True, "message": action.get("description", action_type)}
            else:
                return {"success": False, "message": f"Unknown action: {action_type}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)[:200]}"}

    async def _click_with_healing(self, action: dict) -> dict:
        """Click with multiple fallback strategies."""
        selector = action.get("selector", "")
        description = action.get("description", "")

        # Strategy 1: Direct selector
        try:
            element = self.page.locator(selector).first
            if await element.count() > 0:
                await element.scroll_into_view_if_needed(timeout=5000)
                await element.click(timeout=5000)
                await self._wait_for_settle()
                return {"success": True, "message": f"Clicked: {selector}"}
        except Exception:
            pass

        # Strategy 2: Text-based fallback (extract text from description)
        text_hint = self._extract_text_hint(description)
        if text_hint:
            try:
                text_loc = self.page.get_by_text(text_hint, exact=False).first
                if await text_loc.count() > 0:
                    await text_loc.scroll_into_view_if_needed(timeout=5000)
                    await text_loc.click(timeout=5000)
                    await self._wait_for_settle()
                    return {"success": True, "message": f"Clicked by text: '{text_hint}'"}
            except Exception:
                pass

        # Strategy 3: Scroll down and retry
        try:
            await self.page.mouse.wheel(0, 300)
            await asyncio.sleep(1)
            element = self.page.locator(selector).first
            if await element.count() > 0:
                await element.click(timeout=5000)
                await self._wait_for_settle()
                return {"success": True, "message": f"Clicked after scroll: {selector}"}
        except Exception:
            pass

        # Strategy 4: JavaScript click
        try:
            clicked = await self.page.evaluate(f"""() => {{
                const el = document.querySelector('{selector.replace("'", "\\\\'")}');
                if (el) {{ el.click(); return true; }}
                return false;
            }}""")
            if clicked:
                await self._wait_for_settle()
                return {"success": True, "message": f"JS-clicked: {selector}"}
        except Exception:
            pass

        return {"success": False, "message": f"All click strategies failed for: {selector}"}

    async def _fill_with_healing(self, action: dict) -> dict:
        """Fill input with multiple fallback strategies."""
        selector = action.get("selector", "")
        value = action.get("value", "")

        # Strategy 1: Direct selector
        try:
            element = self.page.locator(selector).first
            if await element.count() > 0:
                await element.scroll_into_view_if_needed(timeout=5000)
                await element.click(timeout=3000)
                await element.fill(value, timeout=5000)
                return {"success": True, "message": f"Filled '{value}' into: {selector}"}
        except Exception:
            pass

        # Strategy 2: By placeholder text
        placeholder = action.get("attrs", {}).get("placeholder", "")
        if placeholder:
            try:
                ph_loc = self.page.get_by_placeholder(placeholder, exact=False).first
                if await ph_loc.count() > 0:
                    await ph_loc.click(timeout=3000)
                    await ph_loc.fill(value, timeout=5000)
                    return {"success": True, "message": f"Filled by placeholder: '{placeholder}'"}
            except Exception:
                pass

        # Strategy 3: By input type
        input_type = ""
        if "email" in selector.lower() or "email" in value.lower():
            input_type = "email"
        elif "password" in selector.lower():
            input_type = "password"

        if input_type:
            try:
                type_loc = self.page.locator(f"input[type='{input_type}']").first
                if await type_loc.count() > 0:
                    await type_loc.click(timeout=3000)
                    await type_loc.fill(value, timeout=5000)
                    return {"success": True, "message": f"Filled by type='{input_type}'"}
            except Exception:
                pass

        # Strategy 4: JavaScript injection
        try:
            filled = await self.page.evaluate(f"""() => {{
                const el = document.querySelector('{selector.replace("'", "\\\\'")}');
                if (el) {{
                    el.value = '{value.replace("'", "\\\\'")}';
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }}
                return false;
            }}""")
            if filled:
                return {"success": True, "message": f"JS-filled '{value}' into: {selector}"}
        except Exception:
            pass

        return {"success": False, "message": f"All fill strategies failed for: {selector}"}

    async def _select(self, action: dict) -> dict:
        selector = action.get("selector", "")
        value = action.get("value", "")
        try:
            await self.page.locator(selector).first.select_option(value, timeout=5000)
            return {"success": True, "message": f"Selected '{value}' in: {selector}"}
        except Exception as e:
            return {"success": False, "message": f"Select failed: {str(e)[:100]}"}

    async def _navigate(self, action: dict) -> dict:
        url = action.get("url", "")
        await self.page.goto(url, wait_until="domcontentloaded")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        return {"success": True, "message": f"Navigated to: {url}"}

    async def _scroll(self, action: dict) -> dict:
        direction = action.get("direction", "down")
        delta = 500 if direction == "down" else -500
        await self.page.mouse.wheel(0, delta)
        await asyncio.sleep(0.5)
        return {"success": True, "message": f"Scrolled {direction}"}

    async def _wait(self, action: dict) -> dict:
        duration = min(action.get("duration", 2000), 15000)
        await asyncio.sleep(duration / 1000)
        return {"success": True, "message": f"Waited {duration}ms"}

    async def _wait_for_settle(self):
        """Wait for page navigation/rendering to settle after action."""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(1)

    @staticmethod
    def _extract_text_hint(description: str) -> str:
        """Try to extract a button/link text from the action description."""
        import re
        patterns = [
            r'"([^"]+)"',       # "Sign Up"
            r"'([^']+)'",       # 'Sign Up'
            r'click(?:ing)?\s+(?:the\s+)?(.+?)(?:\s+button|\s+link)?$',
        ]
        for p in patterns:
            m = re.search(p, description, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    async def fill_otp(self, otp: str) -> dict:
        """Special handler: fill OTP into verification field(s)."""
        # Strategy 1: Single OTP input field
        otp_selectors = [
            "input[type='number']", "input[type='tel']",
            "input.otp", "input.form-control",
            "input[name*='otp']", "input[name*='code']",
            "input[placeholder*='code']", "input[placeholder*='OTP']",
        ]

        for sel in otp_selectors:
            try:
                el = self.page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.click(timeout=3000)
                    await el.fill(otp, timeout=3000)
                    print(f"  [otp] Filled OTP into: {sel}")
                    return {"success": True, "message": f"OTP '{otp}' filled into {sel}"}
            except Exception:
                continue

        # Strategy 2: Multiple individual digit inputs
        try:
            digit_inputs = self.page.locator("input[maxlength='1']")
            count = await digit_inputs.count()
            if count >= len(otp):
                for i, digit in enumerate(otp):
                    await digit_inputs.nth(i).fill(digit, timeout=2000)
                print(f"  [otp] Filled OTP into {count} digit fields")
                return {"success": True, "message": f"OTP '{otp}' filled into {count} digit fields"}
        except Exception:
            pass

        # Strategy 3: JS injection
        try:
            for sel in otp_selectors:
                filled = await self.page.evaluate(f"""() => {{
                    const el = document.querySelector("{sel}");
                    if (el) {{
                        el.value = "{otp}";
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return true;
                    }}
                    return false;
                }}""")
                if filled:
                    return {"success": True, "message": f"OTP '{otp}' JS-filled into {sel}"}
        except Exception:
            pass

        return {"success": False, "message": "Could not find OTP input field"}
