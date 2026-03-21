"""
Autonomous E2E Testing Agent
==============================
Enter any URL + instructions → AI opens browser, tests everything, self-heals on failures.

No pre-written test scripts needed. The AI:
  - Sees the page (vision)
  - Understands your instructions
  - Decides what to do
  - Self-heals when things break
  - Explores beyond your instructions
  - Reports structured results

Usage:
    python agent.py --url https://google.com --task "Search for AI testing tools"
    python agent.py --url https://appypie.com --task "Create an app for a restaurant"
    python agent.py  # launches interactive mode
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from browser_use import Agent, BrowserProfile
from browser_use.llm import ChatOpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def build_task(url: str, instructions: str) -> str:
    """Build the autonomous agent task from URL + user instructions."""

    task = f"""You are a FULLY AUTONOMOUS E2E Testing AI Agent with SELF-HEALING capabilities.

## TARGET
- URL: {url}
- Start by navigating to: {url}

## USER INSTRUCTIONS
{instructions}

## YOUR AUTONOMOUS TESTING PROCESS

### PHASE 1 — Execute User Instructions
Follow the user's instructions above step by step:
- Navigate to the URL first
- Perform each action described
- Verify each step worked before moving to the next
- If a cookie/popup/banner appears at any time, dismiss it immediately

### PHASE 2 — Smart Page Analysis
After completing user instructions, analyze the page:
- Identify all interactive elements (buttons, links, forms, inputs)
- Check if the page loaded correctly (no errors, no blank sections)
- Verify all images loaded (no broken images)
- Check navigation links work

### PHASE 3 — Autonomous Exploration
Go beyond the instructions and test:
- Click top navigation links and verify pages load
- If there's a form, test with empty submission (check validation)
- If there's a search bar, try a search query
- Test browser back/forward navigation
- Look for any error messages or broken elements

## SELF-HEALING RULES
When something fails, DO NOT give up. Follow this recovery process:

1. **Element not found?**
   → Wait 3 seconds, page might still be loading
   → Look for the element using your VISION (don't rely only on selectors)
   → Try scrolling down — element might be below the fold
   → Try clicking a similar element nearby

2. **Page not loading?**
   → Wait up to 15 seconds
   → Try refreshing the page
   → If still broken, note it and move to next step

3. **Popup/modal blocking?**
   → Look for X button, Close button, or "No thanks" link
   → Try pressing Escape key
   → Try clicking outside the popup

4. **Form submission failed?**
   → Check for validation error messages
   → Fix the input and retry
   → Try different input values

5. **Redirect unexpected?**
   → Note the new URL
   → Adapt and continue testing on the new page
   → Use browser back if needed to return

6. **Element clickable but nothing happens?**
   → Try double-click
   → Try JavaScript click via evaluate
   → Move on and note it as a potential bug

## REPORT FORMAT
When done, provide your report in EXACTLY this format:

=== TEST REPORT ===
URL: {url}
Date: [today's date]

STEPS COMPLETED:
- Step 1: [what you did] -> PASS/FAIL [details]
- Step 2: [what you did] -> PASS/FAIL [details]
(continue for all steps)

SELF-HEALING ACTIONS:
- [any recovery actions you took and what triggered them]

AUTONOMOUS DISCOVERIES:
- [things you found by exploring beyond instructions]

BUGS FOUND:
- [any bugs, errors, broken elements you discovered]

OVERALL SCORE: [X/10]
SUMMARY: [1-2 sentence summary]
=== END REPORT ===
"""
    return task


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


async def run_test(url: str, instructions: str, headless: bool = False) -> dict:
    """Run the autonomous E2E testing agent."""

    print(f"\n{'='*60}")
    print(f"  AUTONOMOUS E2E TESTING AGENT")
    print(f"  URL:  {url}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"\nInstructions: {instructions[:200]}...")

    # Build task
    task = build_task(url, instructions)

    # Browser config
    browser_profile = BrowserProfile(
        headless=headless,
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

    # LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Agent
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

    # Run
    print("\nAgent starting...\n")
    start_time = time.time()

    result_data = {
        "status": "unknown",
        "duration_seconds": 0,
        "final_report": "",
        "actions": [],
        "gif_path": gif_path,
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

    # Save report
    save_report(url, result_data)
    return result_data


async def interactive_mode():
    """Interactive mode — ask user for URL and instructions."""
    print("\n" + "=" * 60)
    print("  AUTONOMOUS E2E TESTING AGENT — Interactive Mode")
    print("=" * 60)

    url = input("\nEnter URL to test: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    if not url.startswith("http"):
        url = "https://" + url

    print("\nEnter test instructions (what should the agent do?):")
    print("(Type your instructions, then press Enter twice to start)\n")

    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        lines.append(line)

    instructions = "\n".join(lines)
    if not instructions.strip():
        instructions = "Perform a complete E2E test of this website. Test all navigation, forms, buttons, and interactive elements."

    await run_test(url, instructions)


async def main():
    parser = argparse.ArgumentParser(description="Autonomous E2E Testing Agent")
    parser.add_argument("--url", type=str, help="URL to test")
    parser.add_argument("--task", type=str, help="Test instructions")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()

    if args.url:
        instructions = args.task or "Perform a complete E2E test of this website. Test all navigation, forms, buttons, and interactive elements."
        await run_test(args.url, instructions, args.headless)
    else:
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
