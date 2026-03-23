"""
Autonomous E2E Testing Agent
==============================
Enter any URL + instructions → AI opens browser, tests everything, self-heals on failures.

Supports: Safari (WebKit), Chrome, Edge, Chromium

Usage:
    python agent.py --url https://google.com --task "Search for AI testing tools"
    python agent.py --url https://google.com --browser safari
    python agent.py --url https://google.com --browser chrome
    python agent.py  # launches interactive mode
"""

import argparse
import asyncio
import base64
import json
import os
import time
from datetime import datetime

try:
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
except ImportError:
    pass  # Dependencies not available in Streamlit Cloud

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def build_task(url: str, instructions: str) -> str:
    """Build the autonomous agent task from URL + user instructions."""
    return f"""You are a FULLY AUTONOMOUS E2E Testing AI Agent with SELF-HEALING capabilities.

## TARGET
- URL: {url}

## USER INSTRUCTIONS
{instructions}

## YOUR AUTONOMOUS TESTING PROCESS

### PHASE 1 — Execute User Instructions
Follow the user's instructions step by step.

### PHASE 2 — Autonomous Exploration
After completing instructions, explore:
- Click navigation links and verify pages load
- Test forms with empty submission (check validation)
- Test search bars
- Look for broken elements or errors

## SELF-HEALING RULES
1. Element not found? → Wait, scroll, try alternative selector
2. Page not loading? → Wait 15s, refresh
3. Popup blocking? → Find close/X button, press Escape
4. Form failed? → Read error, fix input, retry
5. Unexpected redirect? → Adapt and continue

## REPORT FORMAT
When done, give your final report:
=== TEST REPORT ===
URL: {url}
STEPS COMPLETED:
- Step N: [what] -> PASS/FAIL
BUGS FOUND:
- [bugs]
SCORE: [X/10]
=== END REPORT ===
"""


def save_report(url: str, result_data: dict):
    """Save test report as JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"report_{timestamp}.json")
    result_data["timestamp"] = timestamp
    result_data["url"] = url
    with open(report_path, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"\nReport saved: {report_path}")
    return report_path


# ─── Safari Agent (Playwright WebKit + GPT-4o Vision) ────────────────────────

async def run_safari_test(url: str, instructions: str, headless: bool = False) -> dict:
    """Run test in Safari (WebKit) using Playwright + GPT-4o vision."""
    from playwright.async_api import async_playwright

    print(f"\n{'='*60}")
    print(f"  AUTONOMOUS E2E TESTING AGENT")
    print(f"  URL:     {url}")
    print(f"  Browser: Safari (WebKit)")
    print(f"  Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    task = build_task(url, instructions)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = time.time()

    result_data = {
        "status": "unknown",
        "duration_seconds": 0,
        "final_report": "",
        "actions": [],
        "browser": "safari",
        "instructions": instructions,
    }

    pw = await async_playwright().start()
    browser = await pw.webkit.launch(headless=headless)
    context = await browser.new_context(
        viewport={"width": 1470, "height": 956},
        device_scale_factor=2,
    )
    page = await context.new_page()

    print(f"\nSafari (WebKit) browser opened!")
    print(f"Navigating to {url}...")

    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    print("Page loaded. AI agent starting...\n")

    chat_history = [
        {"role": "system", "content": task},
    ]

    max_steps = 50
    actions_taken = []

    for step in range(1, max_steps + 1):
        # Take screenshot
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"safari_{timestamp}_step{step}.png")
        await page.screenshot(path=screenshot_path, full_page=False)

        # Encode screenshot for vision
        with open(screenshot_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        # Get page info
        current_url = page.url
        title = await page.title()

        # Ask GPT-4o what to do next
        chat_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Step {step}. Current URL: {current_url} | Title: {title}\n\nLook at the screenshot and decide the next action. Respond in JSON:\n{{\"action\": \"click|type|scroll|navigate|wait|done\", \"selector\": \"css selector\", \"value\": \"text to type or url\", \"reasoning\": \"why\"}}\n\nIf all testing is done, use action 'done' and put your full TEST REPORT in the 'value' field."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": "high"}
                }
            ]
        })

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=chat_history,
                max_tokens=2000,
                temperature=0.0,
            )
            reply = response.choices[0].message.content
            chat_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"  Step {step}: LLM error: {e}")
            continue

        # Parse the action
        try:
            # Extract JSON from reply
            json_start = reply.find("{")
            json_end = reply.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                action_data = json.loads(reply[json_start:json_end])
            else:
                print(f"  Step {step}: No JSON found in reply, skipping")
                continue
        except json.JSONDecodeError:
            print(f"  Step {step}: Failed to parse action JSON")
            continue

        action = action_data.get("action", "")
        selector = action_data.get("selector", "")
        value = action_data.get("value", "")
        reasoning = action_data.get("reasoning", "")

        print(f"  Step {step}: {action} | {selector or value or ''} | {reasoning[:80]}")
        actions_taken.append(f"{action}: {selector or value}")

        # Execute the action
        try:
            if action == "done":
                result_data["final_report"] = value
                print(f"\n{'='*60}")
                print("TEST REPORT")
                print(f"{'='*60}")
                print(value)
                print(f"{'='*60}")
                break

            elif action == "click":
                if selector:
                    await page.click(selector, timeout=5000)
                    await page.wait_for_timeout(2000)

            elif action == "type":
                if selector and value:
                    await page.fill(selector, value)
                    await page.wait_for_timeout(1000)

            elif action == "scroll":
                direction = value.lower() if value else "down"
                if direction == "up":
                    await page.evaluate("window.scrollBy(0, -500)")
                else:
                    await page.evaluate("window.scrollBy(0, 500)")
                await page.wait_for_timeout(1000)

            elif action == "navigate":
                if value:
                    await page.goto(value, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)

            elif action == "wait":
                wait_time = int(value) if value.isdigit() else 3
                await page.wait_for_timeout(wait_time * 1000)

            # Self-healing: dismiss popups/banners
            try:
                for dismiss_selector in [
                    "button:has-text('Accept')", "button:has-text('Ok')",
                    "button:has-text('Close')", "button:has-text('Got it')",
                    "[aria-label='Close']", ".cookie-banner button",
                ]:
                    btn = page.locator(dismiss_selector).first
                    if await btn.is_visible(timeout=500):
                        await btn.click()
                        print(f"    -> Dismissed popup: {dismiss_selector}")
                        break
            except Exception:
                pass

        except Exception as e:
            print(f"    -> Self-healing: {e}")
            # Self-healing: wait and retry
            await page.wait_for_timeout(2000)
            try:
                if action == "click" and selector:
                    # Try JavaScript click as fallback
                    await page.evaluate(f"document.querySelector('{selector}')?.click()")
                    print(f"    -> Retried with JS click")
            except Exception:
                print(f"    -> Skipping failed action, continuing")

    else:
        # Reached max steps without "done"
        result_data["final_report"] = "Agent reached maximum steps without completing."

    elapsed = time.time() - start_time
    result_data["duration_seconds"] = round(elapsed, 1)
    result_data["status"] = "completed"
    result_data["actions"] = actions_taken

    print(f"\nTotal actions: {len(actions_taken)}")
    print(f"Duration: {elapsed:.0f}s")

    # Cleanup
    await browser.close()
    await pw.stop()

    save_report(url, result_data)
    return result_data


# ─── Chromium Agent (browser-use) ────────────────────────────────────────────

async def run_chromium_test(url: str, instructions: str, headless: bool = False,
                            browser: str = "chromium") -> dict:
    """Run test in Chrome/Edge/Chromium using browser-use."""
    from browser_use import Agent, BrowserProfile
    from browser_use.llm import ChatOpenAI

    print(f"\n{'='*60}")
    print(f"  AUTONOMOUS E2E TESTING AGENT")
    print(f"  URL:     {url}")
    print(f"  Browser: {browser}")
    print(f"  Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    task = build_task(url, instructions)

    channel_map = {"chrome": "chrome", "edge": "msedge", "chromium": None}
    channel = channel_map.get(browser, None)

    browser_profile = BrowserProfile(
        headless=headless,
        channel=channel,
        viewport={"width": 1470, "height": 956},
        args=[
            "--start-maximized",
            "--start-fullscreen",
            "--disable-blink-features=AutomationControlled",
            "--ignore-certificate-errors",
            "--window-size=1470,956",
            "--force-device-scale-factor=2",
            "--high-dpi-support=1",
        ],
        window_size={"width": 1470, "height": 956},
        highlight_elements=True,
        wait_between_actions=1.5,
        enable_default_extensions=False,
        minimum_wait_page_load_time=3.0,
        wait_for_network_idle_page_load_time=5.0,
    )

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gif_path = os.path.join(SCREENSHOT_DIR, f"test_{timestamp}.gif")

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=browser_profile,
        max_actions_per_step=4,
        use_vision=True,
        generate_gif=gif_path,
        max_failures=20,
        step_timeout=300,
        llm_timeout=120,
    )

    print(f"\nInstructions: {instructions[:200]}...")
    print("\nAgent starting...\n")
    start_time = time.time()

    result_data = {
        "status": "unknown",
        "duration_seconds": 0,
        "final_report": "",
        "actions": [],
        "gif_path": gif_path,
        "browser": browser,
        "instructions": instructions,
    }

    try:
        result = await agent.run(max_steps=100)
        elapsed = time.time() - start_time
        result_data["duration_seconds"] = round(elapsed, 1)
        result_data["status"] = "completed"

        if result:
            final = result.final_result()
            if final:
                result_data["final_report"] = final
                print(f"\n{'='*60}")
                print("TEST REPORT")
                print(f"{'='*60}")
                print(final)

            actions = result.action_names()
            result_data["actions"] = actions
            print(f"\nTotal actions: {len(actions)}")
            print(f"Duration: {elapsed:.0f}s")

        print(f"{'='*60}")

    except Exception as e:
        elapsed = time.time() - start_time
        result_data["duration_seconds"] = round(elapsed, 1)
        result_data["status"] = "error"
        result_data["error"] = str(e)
        print(f"\nAgent error after {elapsed:.0f}s: {e}")

    save_report(url, result_data)
    return result_data


# ─── Main Router ──────────────────────────────────────────────────────────────

async def run_test(url: str, instructions: str, headless: bool = False,
                   browser: str = "chromium") -> dict:
    """Route to the correct agent based on browser selection."""
    if browser == "safari":
        return await run_safari_test(url, instructions, headless)
    else:
        return await run_chromium_test(url, instructions, headless, browser)


async def interactive_mode():
    """Interactive mode."""
    print("\n" + "=" * 60)
    print("  AUTONOMOUS E2E TESTING AGENT — Interactive Mode")
    print("=" * 60)

    url = input("\nEnter URL to test: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    if not url.startswith("http"):
        url = "https://" + url

    print("\nEnter test instructions (press Enter twice to start):\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)

    instructions = "\n".join(lines) or "Perform a complete E2E test."
    await run_test(url, instructions, browser="chromium")


async def main():
    parser = argparse.ArgumentParser(description="Autonomous E2E Testing Agent")
    parser.add_argument("--url", type=str, help="URL to test")
    parser.add_argument("--task", type=str, help="Test instructions")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--browser", type=str, default="chromium",
                        choices=["chromium", "chrome", "edge", "safari"],
                        help="Browser to use (default: chromium)")
    args = parser.parse_args()

    if args.url:
        instructions = args.task or "Perform a complete E2E test of this website."
        await run_test(args.url, instructions, args.headless, args.browser)
    else:
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
