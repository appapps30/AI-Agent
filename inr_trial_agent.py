#!/usr/bin/env python3
"""
INR Trial Autonomous QA Agent — End-to-end testing of the Appy Pie
INR Trial App creation flow including Razorpay payment.

Flow: Landing → Business Name → Category → Login → Onboarding →
      Pricing → Razorpay Payment → Trial → Dashboard → Editor → Save

Usage:
  python3 inr_trial_agent.py
  python3 inr_trial_agent.py --app-name "MyBiz" --max-steps 40
"""
import asyncio
import argparse
import json
import logging
import sys
import os
import glob
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from config import MAX_STEPS, SCREENSHOT_DIR, OPENAI_API_KEY
from agent.dual_browser import DualBrowser
from agent.chunker import chunk_interactive_elements
from agent.embedder import Embedder
from agent.vector_store import VectorStore
from agent.retriever import Retriever
from agent.stage_planner import StagePlanner
from agent.self_healing_executor import SelfHealingExecutor
from agent.rag_knowledge import RAGKnowledge
from agent.inr_trial_orchestrator import INRTrialOrchestrator

# --- Logging ---
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_filename = os.path.join(LOGS_DIR, f"inr_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger = logging.getLogger("inr_trial_agent")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

BASE_URL = "https://www.appypie.com/app-builder/appmaker"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


def cleanup_screenshots():
    RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
    for d, pattern in [(SCREENSHOT_DIR, "*.png"), (RECORDINGS_DIR, "*.*")]:
        if os.path.exists(d):
            for f in glob.glob(os.path.join(d, pattern)):
                try:
                    os.remove(f)
                except Exception:
                    pass
        os.makedirs(d, exist_ok=True)


async def run_inr_trial_agent(
    app_name: str = None,
    max_steps: int = None,
    email: str = None,
    password: str = None,
):
    max_steps = max_steps or 40
    cleanup_screenshots()

    orchestrator = INRTrialOrchestrator(
        app_name=app_name,
        email=email or "testqa.delhi21@gmail.com",
        password=password or "Test@12345",
    )

    logger.info(f"\n{'='*60}")
    logger.info(f"  INR TRIAL AUTONOMOUS QA AGENT")
    logger.info(f"  Platform: {BASE_URL}")
    logger.info(f"  App Name: {orchestrator.app_name}")
    logger.info(f"  Email:    {orchestrator.email}")
    logger.info(f"  Password: {orchestrator.password}")
    logger.info(f"  Steps:    {max_steps}")
    logger.info(f"  Log:      {log_filename}")
    logger.info(f"{'='*60}\n")

    # --- Initialize ---
    logger.info("[init] Launching browser...")
    browser = DualBrowser()
    await browser.launch()

    logger.info("[init] Loading embedding model + RAG knowledge...")
    embedder = Embedder()
    page_vector_store = VectorStore(embedder)
    retriever = Retriever(page_vector_store)
    rag_knowledge = RAGKnowledge(embedder)
    rag_knowledge.load_knowledge_base(
        os.path.join(os.path.dirname(__file__), "knowledge_base")
    )

    planner = StagePlanner()
    executor = SelfHealingExecutor(browser.main_page)

    # --- Navigate ---
    logger.info(f"\n[step 0] Navigating to {BASE_URL}")
    await browser.main_goto(BASE_URL)

    action_log = []

    try:
        for step in range(1, max_steps + 1):
            await browser._recover_main_page()
            try:
                await browser.main_page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                await asyncio.sleep(2)
                await browser._recover_main_page()
            try:
                await browser.main_page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(1)

            current_url = await browser.main_url()
            executor.page = browser.main_page

            await browser.main_screenshot(step)

            interactive_json = await browser.get_main_interactive_elements()

            page_text = ""
            try:
                page_text = await browser.main_page.evaluate(
                    "() => document.body.innerText.substring(0, 2000)"
                )
            except Exception:
                pass

            # --- Detect stage ---
            stage = orchestrator.detect_stage(current_url, page_text)
            progress = orchestrator.get_progress_summary()

            logger.info(f"\n{'—'*55}")
            logger.info(f"[step {step}] {progress}")
            logger.info(f"  URL: {current_url}")

            # ===================================================
            # SELF-HEALING ENGINE — Auto-handle common patterns
            # ===================================================
            text_lower = page_text.lower()
            json_lower = interactive_json.lower()
            auto_handled = False

            # AUTO 1: Login — step-by-step: email → LOGIN → wait → password → LOGIN
            if stage == "login":
                has_password = 'type="password"' in json_lower
                email_filled = any(
                    a.get("action_type") in ("fill", "auto_login") and "email" in a.get("description", "").lower()
                    and a.get("result") == "success"
                    for a in action_log[-5:]
                )

                if not email_filled:
                    # STEP 1: Click email field, fill email, click LOGIN
                    logger.info(f"  [HEAL] Login Step 1: Filling email")
                    for sel in ['#testing', 'input[placeholder*="Email"]', 'input[name="testing"]']:
                        try:
                            await executor.page.click(sel, timeout=2000)
                            await asyncio.sleep(0.5)
                            await executor.page.fill(sel, orchestrator.email, timeout=3000)
                            logger.info(f"  [HEAL] Filled email via {sel}")
                            break
                        except Exception:
                            continue
                    await asyncio.sleep(1)
                    try:
                        await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                        logger.info(f"  [HEAL] Clicked LOGIN to reveal password")
                    except Exception:
                        pass
                    action_log.append({"step": step, "action_type": "auto_login", "description": "Auto-filled email + clicked LOGIN", "result": "success", "stage": stage})
                    await asyncio.sleep(3)
                    auto_handled = True

                elif has_password:
                    # STEP 2: Click password field, fill password, click LOGIN
                    logger.info(f"  [HEAL] Login Step 2: Filling password")
                    filled = False
                    for sel in ['input[type="password"]', '#password', 'input[placeholder*="Password"]']:
                        try:
                            await executor.page.click(sel, timeout=2000)
                            await asyncio.sleep(0.5)
                            await executor.page.fill(sel, orchestrator.password, timeout=3000)
                            logger.info(f"  [HEAL] Filled password via {sel}")
                            filled = True
                            break
                        except Exception:
                            continue
                    if not filled:
                        try:
                            await executor.page.evaluate(f"""() => {{
                                const el = document.querySelector('input[type="password"]');
                                if (el) {{ el.focus(); el.value = '{orchestrator.password}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
                            }}""")
                            logger.info(f"  [HEAL] JS-filled password")
                        except Exception:
                            pass
                    await asyncio.sleep(1)
                    try:
                        await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                        logger.info(f"  [HEAL] Clicked LOGIN to submit")
                    except Exception:
                        pass
                    action_log.append({"step": step, "action_type": "auto_login", "description": "Auto-filled password + clicked LOGIN", "result": "success", "stage": stage})
                    await asyncio.sleep(3)
                    auto_handled = True

                else:
                    # STEP 1.5: Email filled but password field not detected yet.
                    # Count how many consecutive login steps we've had with email filled
                    login_retries = sum(
                        1 for a in action_log[-6:]
                        if a.get("stage") == "login"
                    )
                    if login_retries < 3:
                        # Try clicking LOGIN again to reveal password field
                        logger.info(f"  [HEAL] Login Step 1.5: Email filled, password not visible — clicking LOGIN again (attempt {login_retries + 1})")
                        try:
                            await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                            logger.info(f"  [HEAL] Clicked LOGIN to reveal password")
                        except Exception:
                            pass
                        await asyncio.sleep(3)
                        action_log.append({"step": step, "action_type": "auto_login", "description": "Re-clicked LOGIN to reveal password field", "result": "success", "stage": stage})
                        auto_handled = True
                    else:
                        # Password field still not detected after retries — try filling it anyway via JS
                        logger.info(f"  [HEAL] Login Step 1.5 FORCE: Trying to fill password via JS after {login_retries} retries")
                        try:
                            # Check for ANY password-like input via JS
                            pw_found = await executor.page.evaluate(f"""() => {{
                                const sels = ['input[type="password"]', '#password', 'input[placeholder*="assword"]', 'input[name*="assword"]'];
                                for (const s of sels) {{
                                    const el = document.querySelector(s);
                                    if (el) {{
                                        el.focus();
                                        el.value = '{orchestrator.password}';
                                        el.dispatchEvent(new Event('input', {{bubbles:true}}));
                                        el.dispatchEvent(new Event('change', {{bubbles:true}}));
                                        return true;
                                    }}
                                }}
                                return false;
                            }}""")
                            if pw_found:
                                logger.info(f"  [HEAL] JS-force-filled password")
                            else:
                                logger.info(f"  [HEAL] No password input found via JS either")
                        except Exception:
                            pass
                        await asyncio.sleep(1)
                        try:
                            await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                            logger.info(f"  [HEAL] Clicked LOGIN to submit")
                        except Exception:
                            pass
                        action_log.append({"step": step, "action_type": "auto_login", "description": "Force-filled password via JS + clicked LOGIN", "result": "success", "stage": stage})
                        await asyncio.sleep(3)
                        auto_handled = True

            # AUTO 2: Signup — if "password is required" visible, fill password + click SIGN UP
            if not auto_handled and stage == "registration":
                if "password is required" in text_lower or ('type="password"' in json_lower):
                    logger.info(f"  [HEAL] Signup: password field detected — auto-filling")
                    for sel in ['input[type="password"]', '#password', 'input[placeholder*="Password"]']:
                        try:
                            await executor.page.fill(sel, orchestrator.password, timeout=3000)
                            logger.info(f"  [HEAL] Filled password via {sel}")
                            break
                        except Exception:
                            continue
                    await asyncio.sleep(1)
                    for sel in ['button:has-text("SIGN UP")', 'button:has-text("Sign Up")']:
                        try:
                            await executor.page.click(sel, timeout=3000)
                            logger.info(f"  [HEAL] Clicked SIGN UP via {sel}")
                            break
                        except Exception:
                            continue
                    action_log.append({"step": step, "action_type": "auto_signup", "description": "Auto-filled password and clicked SIGN UP", "result": "success", "stage": stage})
                    await asyncio.sleep(2)
                    auto_handled = True

            # AUTO 3: Registration page — auto-click Login link
            if not auto_handled and stage == "registration":
                logger.info(f"  [HEAL] Registration: auto-clicking Login link")
                for sel in ['a:has-text("Login")', 'a:has-text("Log in")', 'a[href*="login"]']:
                    try:
                        link = executor.page.locator(sel).first
                        if await link.count() > 0 and await link.is_visible():
                            await link.click(timeout=3000)
                            logger.info(f"  [HEAL] Clicked Login link via {sel}")
                            action_log.append({"step": step, "action_type": "auto_login_redirect", "description": "Auto-clicked Login link on registration page", "result": "success", "stage": stage})
                            await asyncio.sleep(3)
                            auto_handled = True
                            break
                    except Exception:
                        continue

            # AUTO 3.5: Onboarding — select "For Work", then "2-10", then Continue
            if not auto_handled and stage == "onboarding_purpose":
                logger.info(f"  [HEAL] Onboarding: selecting For Work + 2-10")
                # Click "For Work" precisely — target the card text, not a parent div
                for sel in [
                    'text="For Work"',
                    'h3:has-text("For Work")',
                    'p:has-text("For Work")',
                    'span:has-text("For Work")',
                ]:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Selected 'For Work' via {sel}")
                            break
                    except Exception:
                        continue
                await asyncio.sleep(2)

                # Check if "2-10" team size option appeared and click it
                for sel in [
                    'text="2-10"',
                    'span:has-text("2-10")',
                    'div:text-is("2-10")',
                    'label:has-text("2-10")',
                    'button:has-text("2-10")',
                ]:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Selected '2-10' via {sel}")
                            break
                    except Exception:
                        continue
                await asyncio.sleep(1)

                # Click Continue
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext', 'button.btn-primary']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Clicked Continue via {sel}")
                            break
                    except Exception:
                        continue
                action_log.append({"step": step, "action_type": "auto_onboarding", "description": "Selected For Work + 2-10 + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.6: Team Size page — select "2-10" + click Continue
            if not auto_handled and stage == "team_size":
                logger.info(f"  [HEAL] Team Size: selecting 2-10")
                for sel in [
                    'text="2-10"',
                    'span:has-text("2-10")',
                    'div:text-is("2-10")',
                    'p:has-text("2-10")',
                ]:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Selected '2-10' via {sel}")
                            break
                    except Exception:
                        continue
                await asyncio.sleep(1)
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Clicked Continue via {sel}")
                            break
                    except Exception:
                        continue
                action_log.append({"step": step, "action_type": "auto_team_size", "description": "Selected 2-10 + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.7: App Purpose page — select option + click Continue
            if not auto_handled and stage == "app_purpose":
                logger.info(f"  [HEAL] App Purpose: selecting option + Continue")
                # Click "Sell Products & Services Online" card
                for sel in [
                    'text="Sell Products & Services Online"',
                    'span:has-text("Sell Products")',
                    'div:text-is("Sell Products & Services Online")',
                ]:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Selected purpose via {sel}")
                            break
                    except Exception:
                        continue
                await asyncio.sleep(1)
                # Click Continue
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext', 'button.btn-primary']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Clicked Continue via {sel}")
                            break
                    except Exception:
                        continue
                action_log.append({"step": step, "action_type": "auto_purpose", "description": "Selected app purpose + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.7: Upgrade Prompt — click "Upgrade Now"
            if not auto_handled and stage == "upgrade_prompt":
                logger.info(f"  [HEAL] Upgrade Prompt: clicking Upgrade Now")
                for sel in ['button:has-text("Start My 7-days Trial")', 'a:has-text("Start My 7-days Trial")',
                            'button:has-text("Upgrade Now")', 'a:has-text("Upgrade Now")', '.btn-primary']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            logger.info(f"  [HEAL] Clicked Upgrade Now via {sel}")
                            break
                    except Exception:
                        continue
                action_log.append({"step": step, "action_type": "auto_upgrade", "description": "Clicked Upgrade Now", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.9: Trial Congratulations — click "Go to My Business"
            if not auto_handled and stage == "trial_loading":
                if "congratulations" in text_lower or "go to my business" in text_lower:
                    logger.info(f"  [HEAL] Trial ready: clicking Go to My Business")
                    for sel in ['a:has-text("Go to My Business")', 'button:has-text("Go to My Business")',
                                'a:has-text("Go to my Business")', 'a.btn']:
                        try:
                            el = executor.page.locator(sel).first
                            if await el.count() > 0 and await el.is_visible():
                                await el.click(timeout=5000)
                                logger.info(f"  [HEAL] Clicked 'Go to My Business' via {sel}")
                                action_log.append({"step": step, "action_type": "auto_trial", "description": "Clicked Go to My Business", "result": "success", "stage": stage})
                                await asyncio.sleep(5)
                                auto_handled = True
                                break
                        except Exception:
                            continue

            # AUTO 4: Dismiss popups/modals
            if not auto_handled:
                for popup_sel in ['#cookie-accept', 'button:has-text("Accept")', 'button:has-text("Got it")',
                                  'button:has-text("Close")', '.modal-close', 'button[aria-label="Close"]']:
                    try:
                        popup = executor.page.locator(popup_sel).first
                        if await popup.count() > 0 and await popup.is_visible():
                            await popup.click(timeout=2000)
                            logger.info(f"  [HEAL] Dismissed popup: {popup_sel}")
                            break
                    except Exception:
                        continue

            # AUTO 4: Payment page — detect Razorpay iframe and handle
            if not auto_handled and stage == "razorpay_checkout":
                logger.info(f"  [HEAL] Razorpay: looking for iframe")
                try:
                    # Find the Razorpay iframe
                    rzp_frame = None
                    for frame in executor.page.frames:
                        if "razorpay" in frame.url.lower() or "api.razorpay.com" in frame.url.lower():
                            rzp_frame = frame
                            logger.info(f"  [HEAL] Found Razorpay iframe: {frame.url[:80]}")
                            break

                    # Check if contact details already submitted (phone already filled in past actions)
                    contact_done = any(
                        a.get("action_type") == "auto_razorpay" and "phone" in a.get("description", "").lower()
                        and a.get("result") == "success"
                        for a in action_log[-8:]
                    )

                    if contact_done and rzp_frame:
                        # Payment options showing — click "Show QR" if visible, then wait
                        logger.info(f"  [HEAL] Razorpay: contact details done — looking for Show QR button")
                        show_qr_clicked = False
                        for btn_sel in ['button:has-text("Show QR")', 'a:has-text("Show QR")',
                                        'text="Show QR"', 'span:has-text("Show QR")']:
                            try:
                                btn = rzp_frame.locator(btn_sel).first
                                if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                                    await btn.click(timeout=5000)
                                    logger.info(f"  [HEAL] Clicked 'Show QR' via {btn_sel}")
                                    show_qr_clicked = True
                                    break
                            except Exception:
                                continue
                        if not show_qr_clicked:
                            # Try JS fallback
                            try:
                                result = await rzp_frame.evaluate("""() => {
                                    const els = document.querySelectorAll('button, a, span, div');
                                    for (const el of els) {
                                        if (el.innerText && el.innerText.trim().toLowerCase().includes('show qr') && el.offsetParent !== null) {
                                            el.click(); return true;
                                        }
                                    }
                                    return false;
                                }""")
                                if result:
                                    logger.info(f"  [HEAL] JS-clicked 'Show QR'")
                                    show_qr_clicked = True
                            except Exception:
                                pass
                        if show_qr_clicked:
                            action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Clicked Show QR in Razorpay", "result": "success", "stage": stage})
                        else:
                            logger.info(f"  [HEAL] Show QR not found — waiting for payment")
                            action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Waiting for QR payment", "result": "success", "stage": stage})
                        await asyncio.sleep(10)
                        auto_handled = True

                    elif rzp_frame and not auto_handled:
                        # Need to fill contact details first
                        try:
                            phone_field = rzp_frame.locator('input[type="tel"], input[name="contact"]').first
                            if await phone_field.count() > 0:
                                await phone_field.click(timeout=3000)
                                await asyncio.sleep(0.5)
                                await phone_field.fill('', timeout=2000)
                                await phone_field.type('9891347174', delay=50, timeout=5000)
                                logger.info(f"  [HEAL] Typed phone in Razorpay frame")
                                await asyncio.sleep(2)

                                # Click Continue
                                clicked = False
                                for btn_sel in ['button:has-text("Continue")', 'button[type="submit"]',
                                                '#footer button', '.modal button', 'button.btn']:
                                    try:
                                        btn = rzp_frame.locator(btn_sel).first
                                        if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                                            await btn.click(timeout=5000)
                                            logger.info(f"  [HEAL] Clicked Continue in Razorpay frame via {btn_sel}")
                                            clicked = True
                                            break
                                    except Exception:
                                        continue

                                if not clicked:
                                    try:
                                        await rzp_frame.evaluate("""() => {
                                            const btns = document.querySelectorAll('button');
                                            for (const b of btns) {
                                                if (b.offsetParent !== null && b.innerText.toLowerCase().includes('continue')) {
                                                    b.click(); return true;
                                                }
                                            }
                                            for (const b of btns) {
                                                if (b.offsetParent !== null && b.type === 'submit') {
                                                    b.click(); return true;
                                                }
                                            }
                                            return false;
                                        }""")
                                        logger.info(f"  [HEAL] JS-clicked Continue in Razorpay frame")
                                        clicked = True
                                    except Exception as e:
                                        logger.info(f"  [HEAL] JS click fallback failed: {str(e)[:80]}")

                                if clicked:
                                    action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Typed phone + clicked Continue in Razorpay iframe", "result": "success", "stage": stage})
                                    await asyncio.sleep(5)
                                    auto_handled = True
                        except Exception as e:
                            logger.info(f"  [HEAL] Razorpay frame interaction failed: {str(e)[:100]}")

                    if not auto_handled:
                        # Fallback: try main page directly
                        try:
                            await executor.page.fill('input[type="tel"]', '9891347174', timeout=3000)
                            await asyncio.sleep(1)
                            await executor.page.click('button:has-text("Continue")', timeout=3000)
                            action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Filled phone + clicked Continue on main page", "result": "success", "stage": stage})
                            await asyncio.sleep(3)
                            auto_handled = True
                        except Exception:
                            logger.info(f"  [HEAL] Main page Razorpay fallback also failed")

                except Exception as e:
                    logger.info(f"  [HEAL] Razorpay handler error: {str(e)[:150]}")

            # AUTO 5: Stuck detection — same stage for 3+ consecutive steps with failures
            if not auto_handled:
                recent_stages = [a.get("stage") for a in action_log[-3:]]
                recent_fails = sum(1 for a in action_log[-3:] if "failed" in str(a.get("result", "")))
                if len(recent_stages) >= 3 and len(set(recent_stages)) == 1 and recent_fails >= 2:
                    logger.info(f"  [HEAL] Stuck on {stage} for 3+ steps with failures — trying scroll + wait")
                    try:
                        await executor.page.evaluate("window.scrollBy(0, 300)")
                        await asyncio.sleep(2)
                    except Exception:
                        pass

            # AUTO 6: Login-specific stuck detection — same stage for 6+ steps even without failures
            if not auto_handled and stage == "login":
                login_steps = [a for a in action_log[-8:] if a.get("stage") == "login"]
                if len(login_steps) >= 6:
                    logger.info(f"  [HEAL] Login stuck for 6+ steps — forcing full re-login sequence")
                    # Clear the page and start fresh: reload, fill email, click LOGIN, wait, fill password, click LOGIN
                    try:
                        await executor.page.reload(wait_until="domcontentloaded")
                        await asyncio.sleep(3)
                        # Fill email
                        for sel in ['#testing', 'input[placeholder*="Email"]', 'input[name="testing"]']:
                            try:
                                await executor.page.fill(sel, orchestrator.email, timeout=3000)
                                logger.info(f"  [HEAL] Re-filled email via {sel}")
                                break
                            except Exception:
                                continue
                        await asyncio.sleep(1)
                        # Click LOGIN to reveal password
                        await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                        await asyncio.sleep(3)
                        # Now try to fill password
                        pw_filled = False
                        for sel in ['input[type="password"]', '#password', 'input[placeholder*="Password"]']:
                            try:
                                await executor.page.fill(sel, orchestrator.password, timeout=3000)
                                logger.info(f"  [HEAL] Filled password via {sel}")
                                pw_filled = True
                                break
                            except Exception:
                                continue
                        if pw_filled:
                            await asyncio.sleep(1)
                            await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                            logger.info(f"  [HEAL] Submitted login after forced re-login")
                        action_log.append({"step": step, "action_type": "auto_login", "description": "Forced full re-login sequence (email + password + submit)", "result": "success", "stage": stage})
                        await asyncio.sleep(3)
                        auto_handled = True
                    except Exception as e:
                        logger.info(f"  [HEAL] Forced re-login failed: {str(e)[:100]}")

            if auto_handled:
                continue

            # ===================================================
            # NORMAL LLM-DRIVEN FLOW
            # ===================================================

            # --- Chunk + embed ---
            chunks = chunk_interactive_elements(interactive_json)
            page_vector_store.reset()
            page_vector_store.store_chunks(chunks)

            elements_summary = retriever.get_context_summary(
                f"interactive elements for {stage}"
            )
            stage_prompt = orchestrator.get_stage_prompt()
            rag_context = rag_knowledge.query(
                f"{stage} {current_url} next action INR trial"
            )

            # --- Ask LLM ---
            logger.info(f"  Asking LLM (stage: {stage})...")
            action = planner.decide_action(
                current_url, stage_prompt, elements_summary,
                rag_context, action_log, step
            )
            action_type = action.get("action", "unknown")
            description = action.get("description", "")

            # GUARD: Block need_otp at wrong stages
            if action_type == "need_otp" and stage not in ("otp_verify",):
                logger.info(f"  [HEAL] need_otp blocked at stage '{stage}' — overriding to fill email")
                action = {"action": "fill", "selector": "#email", "value": orchestrator.email, "description": "filling email (auto-corrected)"}
                action_type = "fill"
                description = action["description"]

            logger.info(f"  -> {action_type}: {description}")

            # --- DONE ---
            if action_type == "done":
                logger.info(f"\n  DONE: {description}")
                action_log.append({"step": step, "action_type": "done", "description": description, "result": "completed"})
                await browser.main_screenshot(step, "final")
                break

            # --- Execute ---
            result = await executor.execute(action)
            success = result["success"]
            msg = result["message"]
            logger.info(f"  {'OK' if success else 'FAIL'}: {msg}")

            action_log.append({
                "step": step,
                "action_type": action_type,
                "description": description,
                "selector": action.get("selector", ""),
                "url": current_url,
                "stage": stage,
                "result": "success" if success else f"failed: {msg}",
            })

            await asyncio.sleep(1)

        else:
            logger.info(f"\n  Reached max steps ({max_steps})")

    except Exception as e:
        logger.error(f"\n  AGENT ERROR: {str(e)[:300]}")
        action_log.append({"step": 0, "action_type": "error", "description": str(e)[:300], "result": "error"})

    finally:
        successful = sum(1 for a in action_log if a.get("result") == "success")
        failed = sum(1 for a in action_log if "failed" in str(a.get("result", "")))

        report = {
            "timestamp": datetime.now().isoformat(),
            "platform": BASE_URL,
            "app_name": orchestrator.app_name,
            "email": orchestrator.email,
            "total_steps": len(action_log),
            "successful": successful,
            "failed": failed,
            "stages_visited": orchestrator.stage_history,
            "final_stage": orchestrator.current_stage,
            "log_file": log_filename,
            "actions": action_log,
        }

        report_path = os.path.join(os.path.dirname(__file__), "inr_trial_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n  Report:  {report_path}")
        logger.info(f"  Log:     {log_filename}")
        logger.info(f"  Actions: {len(action_log)} ({successful} ok, {failed} failed)")
        logger.info(f"  Stages:  {' -> '.join(orchestrator.stage_history)}")

        # --- Save recording as MP4 ---
        RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        logger.info(f"\n  Saving recording...")

        try:
            video_path = await browser.close()
            if video_path and os.path.exists(video_path):
                import subprocess
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                webm_path = os.path.join(RECORDINGS_DIR, f"recording_{ts}.webm")
                os.rename(video_path, webm_path)
                logger.info(f"  Recording (webm): {webm_path}")

                # Convert to MP4
                mp4_path = os.path.join(RECORDINGS_DIR, f"recording_{ts}.mp4")
                logger.info(f"  Converting to MP4...")
                try:
                    result = subprocess.run(
                        ["ffmpeg", "-y", "-i", webm_path,
                         "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                         "-movflags", "+faststart", mp4_path],
                        capture_output=True, timeout=120
                    )
                    if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                        try:
                            os.remove(webm_path)
                        except Exception:
                            pass
                        logger.info(f"  Recording (mp4): {mp4_path}")
                        report["video"] = mp4_path
                    else:
                        logger.info(f"  MP4 conversion failed — kept webm")
                        report["video"] = webm_path
                except FileNotFoundError:
                    logger.info(f"  ffmpeg not found — kept webm. Install: brew install ffmpeg")
                    report["video"] = webm_path
                except Exception as e:
                    logger.info(f"  Conversion error: {str(e)[:100]} — kept webm")
                    report["video"] = webm_path
            else:
                logger.info(f"  No recording saved")
                report["video"] = None
        except Exception as e:
            logger.error(f"  Recording error: {str(e)[:100]}")
            report["video"] = None

        # Update report with video path
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("\n  Agent finished.\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="INR Trial Autonomous QA Agent")
    parser.add_argument("--app-name", "-a", default=None, help="Business name (random if not provided)")
    parser.add_argument("--max-steps", "-n", type=int, default=40, help="Max steps")
    parser.add_argument("--email", "-e", default=None, help="Login email")
    parser.add_argument("--password", "-p", default=None, help="Login password")
    args = parser.parse_args()

    asyncio.run(run_inr_trial_agent(
        app_name=args.app_name,
        max_steps=args.max_steps,
        email=args.email,
        password=args.password,
    ))


if __name__ == "__main__":
    main()
