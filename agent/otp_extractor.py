"""
OTP Extractor — Uses the helper browser to fetch OTP from Yopmail.
The main browser is NEVER touched.
"""
import re
import asyncio
from playwright.async_api import Page
from config import SCREENSHOT_DIR
import os


class OTPExtractor:
    YOPMAIL_URL = "https://yopmail.com"

    def __init__(self, helper_page: Page):
        self.page = helper_page

    async def get_otp(self, email: str, max_retries: int = 6, retry_delay: int = 10) -> dict:
        """
        Fetch OTP code from Yopmail inbox using the helper browser.

        Returns:
            dict with 'success', 'otp', 'message'
        """
        username = email.split("@")[0]

        try:
            # 1. Navigate to Yopmail
            print(f"  [otp] Opening Yopmail (helper browser)...")
            await self.page.goto(self.YOPMAIL_URL, wait_until="domcontentloaded")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(1)

            # 2. Enter email username
            print(f"  [otp] Checking inbox for: {username}")
            login_input = self.page.locator("#login")
            await login_input.fill(username)
            await asyncio.sleep(0.5)

            # 3. Click check inbox
            try:
                await self.page.locator(
                    "#refreshbut .material-icons-outlined, button[title='Check Inbox']"
                ).first.click()
            except Exception:
                await self.page.keyboard.press("Enter")
            await asyncio.sleep(3)

            # Debug screenshot — see what Yopmail shows
            try:
                os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                await self.page.screenshot(
                    path=os.path.join(SCREENSHOT_DIR, "debug_yopmail_inbox.png"),
                    full_page=False
                )
                print(f"  [otp] Debug screenshot saved: debug_yopmail_inbox.png")
            except Exception:
                pass

            # 4. Retry loop to find OTP email
            for attempt in range(1, max_retries + 1):
                print(f"  [otp] Attempt {attempt}/{max_retries}...")

                # Click the first email in inbox list (left iframe)
                try:
                    inbox_list = self.page.frame_locator("#ifinbox")
                    first_mail = inbox_list.locator("button.lm, div.m").first
                    if await first_mail.count() > 0:
                        await first_mail.click(timeout=3000)
                        await asyncio.sleep(2)
                except Exception:
                    pass

                otp = await self._extract_otp_from_inbox()
                if otp:
                    print(f"  [otp] Found OTP: {otp}")
                    return {"success": True, "otp": otp, "message": f"OTP extracted: {otp}"}

                if attempt < max_retries:
                    print(f"  [otp] No OTP yet, waiting {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    # Refresh inbox
                    try:
                        await self.page.locator("#refresh").click(timeout=3000)
                        await asyncio.sleep(2)
                    except Exception:
                        try:
                            await self.page.goto(
                                f"https://yopmail.com/en/?login={username}",
                                wait_until="domcontentloaded"
                            )
                            await asyncio.sleep(3)
                            # Re-click check inbox button
                            try:
                                await self.page.locator(
                                    "#refreshbut .material-icons-outlined, button[title='Check Inbox']"
                                ).first.click()
                            except Exception:
                                await self.page.keyboard.press("Enter")
                            await asyncio.sleep(3)
                        except Exception:
                            pass

            return {
                "success": False,
                "otp": None,
                "message": f"No OTP found after {max_retries} attempts",
            }

        except Exception as e:
            return {
                "success": False,
                "otp": None,
                "message": f"OTP extraction error: {str(e)[:200]}",
            }

    async def get_verify_link(self, email: str, max_retries: int = 6, retry_delay: int = 10) -> dict:
        """
        Fetch verification link from Yopmail inbox.

        Returns:
            dict with 'success', 'url', 'message'
        """
        username = email.split("@")[0]

        try:
            print(f"  [verify] Opening Yopmail (helper browser)...")
            await self.page.goto(self.YOPMAIL_URL, wait_until="domcontentloaded")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(1)

            login_input = self.page.locator("#login")
            await login_input.fill(username)
            await asyncio.sleep(0.5)

            try:
                await self.page.locator(
                    "#refreshbut .material-icons-outlined, button[title='Check Inbox']"
                ).first.click()
            except Exception:
                await self.page.keyboard.press("Enter")
            await asyncio.sleep(3)

            for attempt in range(1, max_retries + 1):
                print(f"  [verify] Attempt {attempt}/{max_retries}...")

                url = await self._extract_verify_link_from_inbox()
                if url:
                    print(f"  [verify] Found link: {url[:80]}")
                    return {"success": True, "url": url, "message": "Verification link found"}

                if attempt < max_retries:
                    print(f"  [verify] No link yet, waiting {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    try:
                        await self.page.locator("#refresh").click(timeout=3000)
                    except Exception:
                        pass
                    await asyncio.sleep(3)

            return {"success": False, "url": None, "message": f"No verification link found after {max_retries} attempts"}

        except Exception as e:
            return {"success": False, "url": None, "message": f"Error: {str(e)[:200]}"}

    async def _extract_otp_from_inbox(self) -> str | None:
        """Read the email body from Yopmail iframe and extract OTP digits."""
        # Try reading email body (right iframe)
        body_text = ""
        try:
            inbox_frame = self.page.frame_locator("#ifmail")
            body_text = await inbox_frame.locator("body").inner_text(timeout=5000)
            print(f"  [otp] Email body ({len(body_text)} chars): {body_text[:150]}")
        except Exception as e:
            print(f"  [otp] Could not read email body: {str(e)[:80]}")

        # Also try reading from inbox list (left iframe) — sometimes shows OTP in subject
        if not body_text or len(body_text) < 10:
            try:
                inbox_list = self.page.frame_locator("#ifinbox")
                list_text = await inbox_list.locator("body").inner_text(timeout=3000)
                body_text += " " + list_text
                print(f"  [otp] Inbox list text: {list_text[:100]}")
            except Exception:
                pass

        if not body_text:
            return None

        # Look for 4-6 digit OTP codes
        patterns = [
            r'(?:otp|code|verify|verification)[:\s]*(\d{4,6})',  # "OTP: 123456"
            r'(\d{6})',  # any 6 digits
            r'(\d{5})',  # any 5 digits
            r'(\d{4})',  # any 4 digits
        ]

        for pattern in patterns:
            matches = re.findall(pattern, body_text, re.IGNORECASE)
            for match in matches:
                # Filter out years and common non-OTP numbers
                if match not in ("2024", "2025", "2026", "2027", "2028") and not match.startswith("0"):
                    return match

        return None

    async def _extract_verify_link_from_inbox(self) -> str | None:
        """Extract verification URL from email body."""
        try:
            inbox_frame = self.page.frame_locator("#ifmail")
            links = await inbox_frame.locator("a[href]").all()

            verify_keywords = [
                "verify", "confirm", "activate", "validate",
                "registration", "email-verify", "account/confirm", "auth/verify"
            ]

            for link in links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).lower().strip()
                combined = (href + " " + text).lower()

                if any(kw in combined for kw in verify_keywords):
                    if href.startswith("http"):
                        return href

            # Fallback: any link with token/code params
            for link in links:
                href = await link.get_attribute("href") or ""
                if href.startswith("http") and any(
                    kw in href.lower() for kw in ["token=", "code=", "verify", "confirm"]
                ):
                    return href

        except Exception:
            pass
        return None
