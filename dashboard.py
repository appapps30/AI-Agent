"""
Autonomous E2E Testing Agent — Dashboard
Run with: streamlit run dashboard.py
"""

import os
import json
import glob
import subprocess
import threading
import queue
import streamlit as st
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(BASE_DIR, "agent.py")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

st.set_page_config(page_title="Autonomous E2E Testing Agent", page_icon="🤖", layout="wide")

# --- Session State ---
for key, default in {
    "agent_running": False,
    "agent_output": "",
    "agent_queue": queue.Queue(),
    "agent_process": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def stream_output(proc, q):
    try:
        for line in iter(proc.stdout.readline, ""):
            if line:
                q.put(line)
        proc.stdout.close()
        proc.wait()
    except Exception:
        pass
    finally:
        q.put(None)


def drain_queue():
    lines = []
    while True:
        try:
            line = st.session_state.agent_queue.get_nowait()
            if line is None:
                st.session_state.agent_running = False
                break
            lines.append(line)
        except queue.Empty:
            break
    if lines:
        st.session_state.agent_output += "".join(lines)


def load_reports():
    if not os.path.exists(REPORT_DIR):
        return []
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "report_*.json")),
                   key=os.path.getmtime, reverse=True)
    reports = []
    for f in files[:20]:
        try:
            with open(f, "r") as fh:
                reports.append(json.load(fh))
        except Exception:
            pass
    return reports


# --- Header ---
st.title("🤖 Autonomous E2E Testing Agent")
st.caption("Enter any URL + instructions → AI tests it autonomously with self-healing")

# --- Tabs ---
tab_agent, tab_reports, tab_screenshots = st.tabs(
    ["🚀 Run Test", "📊 Reports", "📸 Screenshots"]
)

# --- Tab 1: Run Test ---
with tab_agent:

    # URL input
    test_url = st.text_input(
        "🌐 URL to test",
        placeholder="https://www.google.com",
        help="Enter any website URL to test"
    )

    # Instructions
    instructions = st.text_area(
        "📝 Test Instructions",
        placeholder=(
            "Examples:\n"
            "- Search for 'AI testing tools' and verify results appear\n"
            "- Fill the contact form with test data and submit\n"
            "- Navigate to pricing page and check all plans are visible\n"
            "- Create an account with test email and verify signup works"
        ),
        height=150,
        help="Tell the agent what to test. Leave empty for a full automatic E2E test."
    )

    # Options
    col1, col2 = st.columns(2)
    with col1:
        browser_choice = st.selectbox(
            "🌐 Browser",
            ["chromium", "chrome", "edge", "safari"],
            index=0,
            help="Select which browser to use for testing"
        )
    with col2:
        headless = st.checkbox("Headless mode (no browser window)", value=False)

    # Run / Stop buttons
    col_start, col_stop = st.columns(2)

    with col_start:
        if st.button("🚀 Run Test", type="primary", use_container_width=True,
                      disabled=st.session_state.agent_running or not test_url):
            st.session_state.agent_output = ""
            st.session_state.agent_running = True
            st.session_state.agent_queue = queue.Queue()

            cmd = ["python3", AGENT_SCRIPT, "--url", test_url,
                   "--browser", browser_choice]

            if instructions.strip():
                cmd.extend(["--task", instructions.strip()])

            if headless:
                cmd.append("--headless")

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=BASE_DIR,
            )
            st.session_state.agent_process = proc

            t = threading.Thread(
                target=stream_output,
                args=(proc, st.session_state.agent_queue),
                daemon=True
            )
            t.start()
            st.rerun()

    with col_stop:
        if st.button("⛔ Stop Test", use_container_width=True,
                      disabled=not st.session_state.agent_running):
            if st.session_state.agent_process:
                try:
                    st.session_state.agent_process.kill()
                except Exception:
                    pass
            st.session_state.agent_running = False
            st.rerun()

    # Live output
    if st.session_state.agent_running:
        drain_queue()
        st.info("🔄 Agent is running autonomously...")

    if st.session_state.agent_output:
        st.code(st.session_state.agent_output, language="text")

    if st.session_state.agent_running:
        import time
        time.sleep(2)
        st.rerun()

# --- Tab 2: Reports ---
with tab_reports:
    reports = load_reports()
    if reports:
        for report in reports:
            ts = report.get("timestamp", "unknown")
            url = report.get("url", "unknown")
            status = report.get("status", "unknown")
            duration = report.get("duration_seconds", 0)
            instructions_text = report.get("instructions", "")

            icon = "✅" if status == "completed" else "❌"

            with st.expander(f"{icon} {ts} — {url} ({duration}s)"):
                st.markdown(f"**Instructions:** {instructions_text[:300]}")
                st.markdown(f"**Status:** {status} | **Duration:** {duration}s")

                if report.get("final_report"):
                    st.subheader("Agent Report")
                    st.code(report["final_report"], language="text")

                actions = report.get("actions", [])
                if actions:
                    st.subheader(f"Actions ({len(actions)})")
                    for i, action in enumerate(actions):
                        st.text(f"  {i+1}. {action}")
    else:
        st.info("No reports yet. Run a test to generate one.")

# --- Tab 3: Screenshots ---
with tab_screenshots:
    if os.path.exists(SCREENSHOT_DIR):
        gifs = sorted(glob.glob(os.path.join(SCREENSHOT_DIR, "*.gif")),
                      key=os.path.getmtime, reverse=True)
        pngs = sorted(glob.glob(os.path.join(SCREENSHOT_DIR, "*.png")),
                      key=os.path.getmtime, reverse=True)

        if gifs:
            st.subheader("Test Run Recordings")
            for gif in gifs[:5]:
                fname = os.path.basename(gif)
                mod_time = datetime.fromtimestamp(os.path.getmtime(gif)).strftime("%Y-%m-%d %H:%M")
                st.markdown(f"**{fname}** — {mod_time}")
                try:
                    with open(gif, "rb") as f:
                        gif_bytes = f.read()
                    if gif_bytes:
                        st.image(gif_bytes, use_container_width=True)
                    else:
                        st.warning(f"Skipped empty file: {fname}")
                except Exception as e:
                    st.warning(f"Could not display {fname}: {e}")

        if pngs:
            st.subheader("Screenshots")
            cols = st.columns(3)
            for i, png in enumerate(pngs[:12]):
                with cols[i % 3]:
                    st.image(png, caption=os.path.basename(png), use_container_width=True)

        if not gifs and not pngs:
            st.info("No screenshots yet.")
    else:
        st.info("No screenshots yet. Run a test first.")
