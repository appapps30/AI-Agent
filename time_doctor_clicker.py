#!/usr/bin/env python3
"""
Time Doctor Idle Popup Auto-Clicker
Monitors the screen for the "Start working again" button and clicks it automatically.

Usage:
  python3 time_doctor_clicker.py          # Run in foreground
  python3 time_doctor_clicker.py &         # Run in background
"""
import subprocess
import time
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("td_clicker")

CHECK_INTERVAL = 5  # seconds between checks


def find_and_click_start_working():
    """Use AppleScript to find and click 'Start working again' in any window."""
    # Method 1: Try AppleScript to click the button in Time Doctor
    scripts = [
        # Try clicking button by name in Time Doctor app
        '''
        tell application "System Events"
            set allProcs to every process whose visible is true
            repeat with proc in allProcs
                try
                    tell proc
                        set allWindows to every window
                        repeat with w in allWindows
                            try
                                set btns to every button of w whose name contains "Start working"
                                if (count of btns) > 0 then
                                    click (item 1 of btns)
                                    return "clicked"
                                end if
                            end try
                            -- Also check for sheets/groups
                            try
                                set grps to every group of w
                                repeat with g in grps
                                    set btns to every button of g whose name contains "Start working"
                                    if (count of btns) > 0 then
                                        click (item 1 of btns)
                                        return "clicked"
                                    end if
                                end repeat
                            end try
                        end repeat
                    end tell
                end try
            end repeat
        end tell
        return "not_found"
        ''',
        # Try by title/role
        '''
        tell application "System Events"
            try
                click button "Start working again" of window 1 of (first process whose frontmost is true)
                return "clicked"
            end try
        end tell
        return "not_found"
        ''',
    ]

    for script in scripts:
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            if "clicked" in result.stdout.strip():
                return True
        except Exception:
            continue

    return False


def find_and_click_pyautogui():
    """Fallback: use pyautogui to find the button by text on screen."""
    try:
        import pyautogui
        import pyautogui as pag

        # Take a screenshot and look for the button text using locateOnScreen
        # with a reference image, or use OCR-based approach
        # Since we don't have a reference image, use coordinate-based approach
        # by finding the idle popup window

        # Try to find "Start working again" button by color (green button)
        # The button is green (#4CAF50-ish) with white text
        screenshot = pag.screenshot()
        width, height = screenshot.size

        # Scan for the green button color in the likely area (center of screen)
        import PIL.Image
        pixels = screenshot.load()

        # Look for a cluster of green pixels (the button is ~160x40 green)
        green_clusters = []
        for y in range(height // 4, 3 * height // 4):
            for x in range(width // 4, 3 * width // 4, 5):
                r, g, b = pixels[x, y][:3]
                # Green button color range
                if 60 < r < 120 and 140 < g < 200 and 50 < b < 100:
                    green_clusters.append((x, y))

        if green_clusters:
            # Click the center of the green cluster
            avg_x = sum(p[0] for p in green_clusters) // len(green_clusters)
            avg_y = sum(p[1] for p in green_clusters) // len(green_clusters)
            pag.click(avg_x, avg_y)
            return True

    except Exception as e:
        logger.debug(f"pyautogui fallback failed: {e}")

    return False


def main():
    logger.info("Time Doctor auto-clicker started")
    logger.info(f"Checking every {CHECK_INTERVAL}s for 'Start working again' button")
    logger.info("Press Ctrl+C to stop\n")

    click_count = 0

    while True:
        try:
            # Try AppleScript first (more reliable)
            clicked = find_and_click_start_working()

            if not clicked:
                # Fallback to pyautogui
                clicked = find_and_click_pyautogui()

            if clicked:
                click_count += 1
                logger.info(f"Clicked 'Start working again' (total: {click_count})")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total clicks: {click_count}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
