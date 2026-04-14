#!/usr/bin/env python3
"""
INR Trial Agent Dashboard — Web UI for the INR Trial autonomous QA agent.

Run: python3 dashboard.py
URL: http://localhost:8080
"""
import asyncio
import glob
import json
import os
import sys
import threading
import time
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory

sys.path.insert(0, os.path.dirname(__file__))

from config import SCREENSHOT_DIR, MAX_STEPS
from agent.dual_browser import DualBrowser
from agent.chunker import chunk_interactive_elements
from agent.embedder import Embedder
from agent.vector_store import VectorStore
from agent.retriever import Retriever
from agent.stage_planner import StagePlanner
from agent.self_healing_executor import SelfHealingExecutor
from agent.rag_knowledge import RAGKnowledge
from agent.inr_trial_orchestrator import INRTrialOrchestrator

app = Flask(__name__)

agent_state = {
    "running": False,
    "logs": [],
    "report": None,
    "test_email": "",
    "app_name": "",
    "current_step": 0,
    "current_stage": "",
    "screenshots": [],
    "video_file": None,
}

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INR Trial Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #dc2626 0%, #ea580c 100%); padding: 24px 40px; }
        .header h1 { font-size: 28px; font-weight: 700; }
        .header p { opacity: 0.8; margin-top: 4px; }
        .main { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }
        .input-section { background: #1e293b; border-radius: 12px; padding: 28px; margin-bottom: 24px; border: 1px solid #334155; }
        .input-row { display: flex; gap: 12px; margin-bottom: 16px; align-items: flex-end; }
        .input-row.last { margin-bottom: 0; }
        label { display: block; font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        input { width: 100%; padding: 12px 16px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; font-size: 15px; }
        input:focus { outline: none; border-color: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.2); }
        .btn { padding: 12px 28px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-run { background: #22c55e; color: #0f172a; }
        .btn-run:hover { background: #16a34a; }
        .btn-run:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
        .btn-stop { background: #ef4444; color: white; }
        .btn-clear { background: #334155; color: #94a3b8; }
        .info-bar { display: flex; gap: 16px; margin-bottom: 24px; }
        .info-card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px 20px; flex: 1; }
        .info-card .label { font-size: 12px; color: #64748b; text-transform: uppercase; }
        .info-card .value { font-size: 20px; font-weight: 700; margin-top: 4px; }
        .info-card .value.green { color: #22c55e; }
        .info-card .value.blue { color: #3b82f6; }
        .info-card .value.red { color: #ef4444; }
        .info-card .value.orange { color: #f97316; }
        .tabs { display: flex; gap: 0; margin-bottom: 24px; background: #1e293b; border-radius: 12px 12px 0 0; overflow: hidden; border: 1px solid #334155; border-bottom: none; }
        .tab { padding: 14px 28px; font-size: 14px; font-weight: 600; cursor: pointer; color: #64748b; border-bottom: 3px solid transparent; }
        .tab:hover { color: #e2e8f0; background: #334155; }
        .tab.active { color: #ef4444; border-bottom-color: #ef4444; background: #334155; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .browser-view { background: #1e293b; border: 1px solid #334155; border-radius: 0 0 12px 12px; overflow: hidden; }
        .browser-bar { background: #0f172a; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #334155; }
        .browser-dots { display: flex; gap: 6px; }
        .browser-dots span { width: 12px; height: 12px; border-radius: 50%; }
        .browser-dots .red { background: #ef4444; }
        .browser-dots .yellow { background: #eab308; }
        .browser-dots .green { background: #22c55e; }
        .browser-url { flex: 1; background: #1e293b; padding: 6px 12px; border-radius: 6px; font-size: 13px; color: #94a3b8; font-family: monospace; }
        .browser-live-badge { background: #ef444433; color: #ef4444; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .browser-frame { background: #000; min-height: 500px; display: flex; align-items: center; justify-content: center; }
        .browser-frame img { width: 100%; height: auto; display: block; }
        .browser-placeholder { color: #475569; font-size: 16px; text-align: center; padding: 40px; }
        .panel { background: #1e293b; border: 1px solid #334155; border-radius: 12px; overflow: hidden; }
        .panel-header { padding: 14px 20px; background: #334155; font-weight: 600; font-size: 14px; }
        .log-container { height: 500px; overflow-y: auto; padding: 16px; font-family: monospace; font-size: 13px; line-height: 1.8; }
        .log-step { color: #3b82f6; font-weight: 600; }
        .log-action { color: #22c55e; }
        .log-error { color: #ef4444; }
        .log-info { color: #94a3b8; }
        .log-done { color: #eab308; font-weight: 600; }
        .log-stage { color: #f97316; font-weight: 600; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-family: monospace; margin-left: 12px; }
        .badge-email { background: #7c3aed33; color: #a78bfa; }
        .badge-app { background: #22c55e22; color: #22c55e; }
        .video-section { margin-top: 24px; }
        .video-container { background: #1e293b; border: 1px solid #334155; border-radius: 12px; overflow: hidden; }
        .video-container video { width: 100%; }
        .btn-download { background: #3b82f6; color: white; padding: 8px 20px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; text-decoration: none; display: inline-block; margin: 12px 16px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>INR Trial Autonomous Agent</h1>
        <p>End-to-end testing: Landing -> App Creation -> Login -> Payment -> Dashboard -> Editor</p>
    </div>
    <div class="main">
        <div class="input-section">
            <div class="input-row">
                <div style="flex:2;">
                    <label>Email</label>
                    <input type="text" id="email" value="testqa.delhi21@gmail.com">
                </div>
                <div style="flex:1;">
                    <label>Password</label>
                    <input type="password" id="password" value="Test@12345">
                </div>
                <div style="flex:1;">
                    <label>Max Steps</label>
                    <input type="number" id="maxSteps" value="40" min="1" max="100">
                </div>
            </div>
            <div class="input-row last">
                <button class="btn btn-run" id="runBtn" onclick="startAgent()">Run Agent</button>
                <button class="btn btn-stop" id="stopBtn" onclick="stopAgent()" style="display:none;">Stop</button>
                <button class="btn btn-clear" onclick="clearLogs()">Clear</button>
                <span id="appBadge" class="badge badge-app" style="display:none;"></span>
                <span id="emailBadge" class="badge badge-email" style="display:none;"></span>
            </div>
        </div>
        <div class="info-bar">
            <div class="info-card"><div class="label">Status</div><div class="value blue" id="statusValue">Ready</div></div>
            <div class="info-card"><div class="label">Stage</div><div class="value orange" id="stageValue">-</div></div>
            <div class="info-card"><div class="label">Step</div><div class="value green" id="stepValue">0</div></div>
            <div class="info-card"><div class="label">Success</div><div class="value green" id="successValue">0</div></div>
            <div class="info-card"><div class="label">Failed</div><div class="value red" id="failValue">0</div></div>
        </div>
        <div class="tabs">
            <div class="tab active" onclick="switchTab('browser')">Browser</div>
            <div class="tab" onclick="switchTab('logs')">Logs</div>
            <div class="tab" onclick="switchTab('screenshots')">Screenshots</div>
        </div>
        <div class="tab-content active" id="tab-browser">
            <div class="browser-view">
                <div class="browser-bar">
                    <div class="browser-dots"><span class="red"></span><span class="yellow"></span><span class="green"></span></div>
                    <div class="browser-url" id="browserUrl">about:blank</div>
                    <span class="browser-live-badge" id="liveBadge" style="display:none;">LIVE</span>
                </div>
                <div class="browser-frame" id="browserFrame">
                    <div class="browser-placeholder" id="browserPlaceholder">Click "Run Agent" to start</div>
                    <img id="browserImg" src="" style="display:none;" alt="Live view">
                </div>
            </div>
        </div>
        <div class="tab-content" id="tab-logs">
            <div class="panel">
                <div class="panel-header">Agent Logs</div>
                <div class="log-container" id="logContainer"></div>
            </div>
        </div>
        <div class="tab-content" id="tab-screenshots">
            <div class="panel">
                <div class="panel-header">Screenshots</div>
                <div style="display:flex;flex-wrap:wrap;gap:12px;padding:16px;" id="screenshotGrid">
                    <p style="color:#64748b;text-align:center;padding:40px;width:100%;">Screenshots appear here once the agent starts.</p>
                </div>
            </div>
        </div>
        <div class="video-section" id="videoSection" style="display:none;">
            <div class="video-container">
                <div class="panel-header">Recording</div>
                <video id="videoPlayer" controls></video>
                <a id="videoDownload" class="btn-download" download>Download MP4</a>
            </div>
        </div>
    </div>
    <script>
        let pollInterval = null;
        let lastLogCount = 0;

        function startAgent() {
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            const maxSteps = document.getElementById('maxSteps').value;
            document.getElementById('runBtn').disabled = true;
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('statusValue').textContent = 'Starting...';
            document.getElementById('statusValue').className = 'value orange';
            lastLogCount = 0;

            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password, max_steps: parseInt(maxSteps)})
            }).then(r => r.json()).then(data => {
                if (data.email) { document.getElementById('emailBadge').textContent = data.email; document.getElementById('emailBadge').style.display = 'inline-block'; }
                if (data.app_name) { document.getElementById('appBadge').textContent = data.app_name; document.getElementById('appBadge').style.display = 'inline-block'; }
                pollInterval = setInterval(pollStatus, 1500);
            });
        }
        function stopAgent() { fetch('/api/stop', {method: 'POST'}); }
        function clearLogs() {
            document.getElementById('logContainer').innerHTML = '';
            document.getElementById('screenshotGrid').innerHTML = '<p style="color:#64748b;text-align:center;padding:40px;width:100%;">Screenshots appear here once the agent starts.</p>';
            ['stepValue','successValue','failValue'].forEach(id => document.getElementById(id).textContent = '0');
            document.getElementById('statusValue').textContent = 'Ready';
            document.getElementById('stageValue').textContent = '-';
            document.getElementById('emailBadge').style.display = 'none';
            document.getElementById('appBadge').style.display = 'none';
            document.getElementById('videoSection').style.display = 'none';
            document.getElementById('browserImg').style.display = 'none';
            document.getElementById('browserPlaceholder').style.display = 'block';
            document.getElementById('liveBadge').style.display = 'none';
            lastLogCount = 0;
        }
        function pollStatus() {
            fetch('/api/status').then(r => r.json()).then(data => {
                document.getElementById('stepValue').textContent = data.current_step;
                document.getElementById('stageValue').textContent = data.current_stage || '-';
                document.getElementById('successValue').textContent = data.success_count;
                document.getElementById('failValue').textContent = data.fail_count;
                if (data.running) {
                    document.getElementById('statusValue').textContent = 'Running';
                    document.getElementById('statusValue').className = 'value green';
                    document.getElementById('liveBadge').style.display = 'inline-block';
                    const img = document.getElementById('browserImg');
                    img.src = '/screenshot/live?' + Date.now();
                    img.style.display = 'block';
                    document.getElementById('browserPlaceholder').style.display = 'none';
                } else {
                    document.getElementById('statusValue').textContent = 'Finished';
                    document.getElementById('statusValue').className = 'value blue';
                    document.getElementById('runBtn').disabled = false;
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('liveBadge').style.display = 'none';
                    clearInterval(pollInterval);
                    if (data.video_file) {
                        document.getElementById('videoSection').style.display = 'block';
                        document.getElementById('videoPlayer').src = '/recording/' + data.video_file;
                        document.getElementById('videoDownload').href = '/recording/' + data.video_file;
                    }
                }
                const logContainer = document.getElementById('logContainer');
                if (data.logs.length > lastLogCount) {
                    for (let i = lastLogCount; i < data.logs.length; i++) {
                        const div = document.createElement('div');
                        div.className = data.logs[i].type;
                        div.textContent = data.logs[i].text;
                        logContainer.appendChild(div);
                    }
                    lastLogCount = data.logs.length;
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
                if (data.screenshots.length > 0) {
                    const grid = document.getElementById('screenshotGrid');
                    grid.innerHTML = '';
                    data.screenshots.forEach(s => {
                        const img = document.createElement('img');
                        img.src = '/screenshot/' + s;
                        img.style = 'width:200px;border-radius:8px;border:1px solid #334155;cursor:pointer;';
                        img.onclick = () => window.open('/screenshot/' + s);
                        grid.appendChild(img);
                    });
                }
            });
        }
        function switchTab(name) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }
    </script>
</body>
</html>
"""


def add_log(text, log_type="log-info"):
    agent_state["logs"].append({"text": text, "type": log_type, "time": datetime.now().isoformat()})


def cleanup():
    for d in [SCREENSHOT_DIR, RECORDINGS_DIR]:
        if os.path.exists(d):
            for f in glob.glob(os.path.join(d, "*.*")):
                try: os.remove(f)
                except: pass
        os.makedirs(d, exist_ok=True)


async def run_agent_async(email, password, max_steps):
    agent_state["running"] = True
    agent_state["logs"] = []
    agent_state["screenshots"] = []
    agent_state["current_step"] = 0
    agent_state["current_stage"] = ""
    agent_state["report"] = None
    agent_state["video_file"] = None
    cleanup()

    max_steps = max_steps or 40

    # File logger
    LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_filename = os.path.join(LOGS_DIR, f"inr_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_logger = logging.getLogger(f"inr_dashboard_{datetime.now().timestamp()}")
    file_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_filename, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    file_logger.addHandler(fh)

    def log(text, log_type="log-info"):
        add_log(text, log_type)
        file_logger.info(text)

    orchestrator = INRTrialOrchestrator(email=email, password=password)
    agent_state["test_email"] = orchestrator.email
    agent_state["app_name"] = orchestrator.app_name

    log(f"INR TRIAL AGENT", "log-stage")
    log(f"App Name: {orchestrator.app_name}", "log-info")
    log(f"Email: {orchestrator.email}", "log-stage")
    log(f"Log: {log_filename}", "log-info")

    log("Launching browser...", "log-info")
    browser = DualBrowser()
    await browser.launch()

    log("Loading embedding model + RAG knowledge...", "log-info")
    embedder = Embedder()
    page_vector_store = VectorStore(embedder)
    retriever = Retriever(page_vector_store)
    rag_knowledge = RAGKnowledge(embedder)
    rag_knowledge.load_knowledge_base(os.path.join(os.path.dirname(__file__), "knowledge_base"))

    planner = StagePlanner()
    executor = SelfHealingExecutor(browser.main_page)

    url = "https://www.appypie.com/app-builder/appmaker"
    log(f"Navigating to {url}", "log-step")
    await browser.main_goto(url)

    action_log = []

    try:
        for step in range(1, max_steps + 1):
            if not agent_state["running"]:
                log("Agent stopped by user.", "log-error")
                break

            await browser._recover_main_page()
            try: await browser.main_page.wait_for_load_state("domcontentloaded", timeout=10000)
            except: await asyncio.sleep(2); await browser._recover_main_page()
            try: await browser.main_page.wait_for_load_state("networkidle", timeout=10000)
            except: pass
            await asyncio.sleep(1)

            agent_state["current_step"] = step
            current_url = await browser.main_url()
            executor.page = browser.main_page

            await browser.main_screenshot(step)
            agent_state["screenshots"].append(f"step_{step:03d}.png")

            interactive_json = await browser.get_main_interactive_elements()
            page_text = ""
            try: page_text = await browser.main_page.evaluate("() => document.body.innerText.substring(0, 2000)")
            except: pass

            # ===== SELF-HEALING ENGINE =====
            text_lower = page_text.lower()
            json_lower = interactive_json.lower()
            stage = orchestrator.detect_stage(current_url, page_text)
            agent_state["current_stage"] = stage
            auto_handled = False

            log(f"[Step {step}] {orchestrator.get_progress_summary()}", "log-step")
            log(f"  URL: {current_url[:80]}", "log-info")

            # AUTO 1: Login — step-by-step with third branch + JS force-fill
            if stage == "login":
                has_password = 'type="password"' in json_lower
                email_filled = any(a.get("action_type") in ("fill", "auto_login") and "email" in a.get("description", "").lower() and a.get("result") == "success" for a in action_log[-5:])

                if not email_filled:
                    log(f"  [HEAL] Login Step 1: Filling email", "log-action")
                    for sel in ['#testing', 'input[placeholder*="Email"]', 'input[name="testing"]']:
                        try:
                            await executor.page.click(sel, timeout=2000)
                            await asyncio.sleep(0.5)
                            await executor.page.fill(sel, orchestrator.email, timeout=3000)
                            log(f"  [HEAL] Filled email via {sel}", "log-action")
                            break
                        except: continue
                    await asyncio.sleep(1)
                    try: await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                    except: pass
                    log(f"  [HEAL] Clicked LOGIN to reveal password", "log-action")
                    action_log.append({"step": step, "action_type": "auto_login", "description": "Auto-filled email + clicked LOGIN", "result": "success", "stage": stage})
                    await asyncio.sleep(3)
                    auto_handled = True

                elif has_password:
                    log(f"  [HEAL] Login Step 2: Filling password", "log-action")
                    filled = False
                    for sel in ['input[type="password"]', '#password', 'input[placeholder*="Password"]']:
                        try:
                            await executor.page.click(sel, timeout=2000)
                            await asyncio.sleep(0.5)
                            await executor.page.fill(sel, orchestrator.password, timeout=3000)
                            log(f"  [HEAL] Filled password via {sel}", "log-action")
                            filled = True
                            break
                        except: continue
                    if not filled:
                        try:
                            await executor.page.evaluate(f"""() => {{
                                const el = document.querySelector('input[type="password"]');
                                if (el) {{ el.focus(); el.value = '{orchestrator.password}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
                            }}""")
                            log(f"  [HEAL] JS-filled password", "log-action")
                        except: pass
                    await asyncio.sleep(1)
                    try: await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                    except: pass
                    log(f"  [HEAL] Clicked LOGIN to submit", "log-action")
                    action_log.append({"step": step, "action_type": "auto_login", "description": "Auto-filled password + clicked LOGIN", "result": "success", "stage": stage})
                    await asyncio.sleep(3)
                    auto_handled = True

                else:
                    # Email filled but password not visible — retry or force-fill
                    login_retries = sum(1 for a in action_log[-6:] if a.get("stage") == "login")
                    if login_retries < 3:
                        log(f"  [HEAL] Login Step 1.5: clicking LOGIN again (attempt {login_retries + 1})", "log-action")
                        try: await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                        except: pass
                        await asyncio.sleep(3)
                        action_log.append({"step": step, "action_type": "auto_login", "description": "Re-clicked LOGIN to reveal password", "result": "success", "stage": stage})
                        auto_handled = True
                    else:
                        log(f"  [HEAL] Login FORCE: JS-filling password after {login_retries} retries", "log-action")
                        try:
                            await executor.page.evaluate(f"""() => {{
                                const sels = ['input[type="password"]', '#password', 'input[placeholder*="assword"]'];
                                for (const s of sels) {{
                                    const el = document.querySelector(s);
                                    if (el) {{ el.focus(); el.value = '{orchestrator.password}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); el.dispatchEvent(new Event('change', {{bubbles:true}})); return true; }}
                                }}
                                return false;
                            }}""")
                            log(f"  [HEAL] JS-force-filled password", "log-action")
                        except: pass
                        await asyncio.sleep(1)
                        try: await executor.page.click('button:has-text("LOGIN")', timeout=3000)
                        except: pass
                        action_log.append({"step": step, "action_type": "auto_login", "description": "Force-filled password + clicked LOGIN", "result": "success", "stage": stage})
                        await asyncio.sleep(3)
                        auto_handled = True

            # AUTO 2: Registration — signup password or click Login
            if not auto_handled and stage == "registration":
                if "password is required" in text_lower or 'type="password"' in json_lower:
                    log(f"  [HEAL] Auto-filling signup password", "log-action")
                    for sel in ['input[type="password"]', '#password']:
                        try: await executor.page.fill(sel, orchestrator.password, timeout=3000); break
                        except: continue
                    await asyncio.sleep(1)
                    try: await executor.page.click('button:has-text("SIGN UP")', timeout=3000)
                    except: pass
                    action_log.append({"step": step, "action_type": "auto_signup", "description": "Auto-filled password + SIGN UP", "result": "success", "stage": stage})
                    await asyncio.sleep(2)
                    auto_handled = True
                else:
                    for sel in ['a:has-text("Login")', 'a:has-text("Log in")', 'a[href*="login"]']:
                        try:
                            link = executor.page.locator(sel).first
                            if await link.count() > 0 and await link.is_visible():
                                await link.click(timeout=3000)
                                log(f"  [HEAL] Clicked Login link via {sel}", "log-action")
                                action_log.append({"step": step, "action_type": "auto_login_redirect", "description": "Clicked Login link", "result": "success", "stage": stage})
                                await asyncio.sleep(3)
                                auto_handled = True
                                break
                        except: continue

            # AUTO 3: Onboarding — For Work + Continue
            if not auto_handled and stage == "onboarding_purpose":
                log(f"  [HEAL] Onboarding: selecting For Work", "log-action")
                for sel in ['text="For Work"', 'h3:has-text("For Work")', 'p:has-text("For Work")']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Selected 'For Work' via {sel}", "log-action")
                            break
                    except: continue
                await asyncio.sleep(2)
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Clicked Continue via {sel}", "log-action")
                            break
                    except: continue
                action_log.append({"step": step, "action_type": "auto_onboarding", "description": "Selected For Work + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.5: Team Size — select 2-10
            if not auto_handled and stage == "team_size":
                log(f"  [HEAL] Team Size: selecting 2-10", "log-action")
                for sel in ['text="2-10"', 'span:has-text("2-10")', 'div:text-is("2-10")']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Selected '2-10' via {sel}", "log-action")
                            break
                    except: continue
                await asyncio.sleep(1)
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Clicked Continue via {sel}", "log-action")
                            break
                    except: continue
                action_log.append({"step": step, "action_type": "auto_team_size", "description": "Selected 2-10 + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.6: App Purpose — select option + Continue
            if not auto_handled and stage == "app_purpose":
                log(f"  [HEAL] App Purpose: selecting option", "log-action")
                for sel in ['text="Sell Products & Services Online"', 'span:has-text("Sell Products")']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Selected purpose via {sel}", "log-action")
                            break
                    except: continue
                await asyncio.sleep(1)
                for sel in ['button:has-text("Continue")', 'a:has-text("Continue")', '#btnNext']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Clicked Continue via {sel}", "log-action")
                            break
                    except: continue
                action_log.append({"step": step, "action_type": "auto_purpose", "description": "Selected purpose + Continue", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.7: Upgrade Prompt — Start Trial
            if not auto_handled and stage == "upgrade_prompt":
                log(f"  [HEAL] Upgrade: clicking Start Trial", "log-action")
                for sel in ['button:has-text("Start My 7-days Trial")', 'a:has-text("Start My 7-days Trial")',
                            'button:has-text("Upgrade Now")', 'a:has-text("Upgrade Now")', '.btn-primary']:
                    try:
                        el = executor.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.click(timeout=3000)
                            log(f"  [HEAL] Clicked via {sel}", "log-action")
                            break
                    except: continue
                action_log.append({"step": step, "action_type": "auto_upgrade", "description": "Clicked Start Trial", "result": "success", "stage": stage})
                await asyncio.sleep(3)
                auto_handled = True

            # AUTO 3.8: Trial Congratulations — Go to My Business
            if not auto_handled and stage == "trial_loading":
                if "congratulations" in text_lower or "go to my business" in text_lower:
                    log(f"  [HEAL] Trial ready: clicking Go to My Business", "log-action")
                    for sel in ['a:has-text("Go to My Business")', 'button:has-text("Go to My Business")', 'a.btn']:
                        try:
                            el = executor.page.locator(sel).first
                            if await el.count() > 0 and await el.is_visible():
                                await el.click(timeout=5000)
                                log(f"  [HEAL] Clicked 'Go to My Business' via {sel}", "log-action")
                                action_log.append({"step": step, "action_type": "auto_trial", "description": "Clicked Go to My Business", "result": "success", "stage": stage})
                                await asyncio.sleep(5)
                                auto_handled = True
                                break
                        except: continue

            # AUTO 4: Razorpay — iframe handling
            if not auto_handled and stage == "razorpay_checkout":
                log(f"  [HEAL] Razorpay: looking for iframe", "log-action")
                try:
                    rzp_frame = None
                    for frame in executor.page.frames:
                        if "razorpay" in frame.url.lower() or "api.razorpay.com" in frame.url.lower():
                            rzp_frame = frame
                            log(f"  [HEAL] Found Razorpay iframe", "log-action")
                            break
                    contact_done = any(a.get("action_type") == "auto_razorpay" and "phone" in a.get("description", "").lower() and a.get("result") == "success" for a in action_log[-8:])

                    if contact_done and rzp_frame:
                        log(f"  [HEAL] Looking for Show QR button", "log-action")
                        for btn_sel in ['button:has-text("Show QR")', 'a:has-text("Show QR")', 'text="Show QR"']:
                            try:
                                btn = rzp_frame.locator(btn_sel).first
                                if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                                    await btn.click(timeout=5000)
                                    log(f"  [HEAL] Clicked 'Show QR' via {btn_sel}", "log-action")
                                    break
                            except: continue
                        action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Clicked Show QR / waiting for payment", "result": "success", "stage": stage})
                        await asyncio.sleep(10)
                        auto_handled = True

                    elif rzp_frame and not auto_handled:
                        try:
                            phone_field = rzp_frame.locator('input[type="tel"], input[name="contact"]').first
                            if await phone_field.count() > 0:
                                await phone_field.click(timeout=3000)
                                await asyncio.sleep(0.5)
                                await phone_field.fill('', timeout=2000)
                                await phone_field.type('9891347174', delay=50, timeout=5000)
                                log(f"  [HEAL] Typed phone in Razorpay frame", "log-action")
                                await asyncio.sleep(2)
                                for btn_sel in ['button:has-text("Continue")', 'button[type="submit"]']:
                                    try:
                                        btn = rzp_frame.locator(btn_sel).first
                                        if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                                            await btn.click(timeout=5000)
                                            log(f"  [HEAL] Clicked Continue in Razorpay", "log-action")
                                            break
                                    except: continue
                                action_log.append({"step": step, "action_type": "auto_razorpay", "description": "Typed phone + clicked Continue", "result": "success", "stage": stage})
                                await asyncio.sleep(5)
                                auto_handled = True
                        except Exception as e:
                            log(f"  [HEAL] Razorpay error: {str(e)[:80]}", "log-error")
                except Exception as e:
                    log(f"  [HEAL] Razorpay handler error: {str(e)[:100]}", "log-error")

            # AUTO 5: Dismiss popups
            if not auto_handled:
                for sel in ['#cookie-accept', 'button:has-text("Accept")', 'button:has-text("Got it")', 'button:has-text("Close")']:
                    try:
                        p = executor.page.locator(sel).first
                        if await p.count() > 0 and await p.is_visible(): await p.click(timeout=2000); log(f"  [HEAL] Dismissed: {sel}", "log-info"); break
                    except: continue

            if auto_handled:
                continue

            # ===== LLM-DRIVEN FLOW =====
            chunks = chunk_interactive_elements(interactive_json)
            page_vector_store.reset()
            page_vector_store.store_chunks(chunks)
            elements_summary = retriever.get_context_summary(f"interactive elements for {stage}")
            stage_prompt = orchestrator.get_stage_prompt()
            rag_context = rag_knowledge.query(f"{stage} {current_url} next action INR trial")

            log(f"  Asking LLM (stage: {stage})...", "log-info")
            try:
                action = planner.decide_action(current_url, stage_prompt, elements_summary, rag_context, action_log, step)
            except Exception as e:
                log(f"  LLM error: {str(e)[:150]}", "log-error")
                continue

            action_type = action.get("action", "unknown")
            description = action.get("description", "")

            if action_type == "need_otp" and stage not in ("otp_verify",):
                action = {"action": "fill", "selector": "#testing", "value": orchestrator.email, "description": "filling email (auto-corrected)"}
                action_type = "fill"
                description = action["description"]

            log(f"  -> {action_type}: {description}", "log-action")

            if action_type == "done":
                log(f"DONE: {description}", "log-done")
                action_log.append({"step": step, "action_type": "done", "description": description, "result": "completed"})
                break

            result = await executor.execute(action)
            success = result["success"]
            log(f"  {'OK' if success else 'FAIL'}: {result['message']}", "log-action" if success else "log-error")
            action_log.append({"step": step, "action_type": action_type, "description": description, "selector": action.get("selector", ""), "url": current_url, "stage": stage, "result": "success" if success else f"failed: {result['message']}"})
            await asyncio.sleep(1)
        else:
            log(f"Reached max steps ({max_steps})", "log-done")

    except Exception as e:
        log(f"Agent error: {str(e)[:300]}", "log-error")
    finally:
        agent_state["report"] = action_log
        agent_state["running"] = False
        log("Saving recording...", "log-info")
        try:
            video_path = await browser.close()
            if video_path and os.path.exists(video_path):
                import subprocess
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                webm_path = os.path.join(RECORDINGS_DIR, f"recording_{ts}.webm")
                os.rename(video_path, webm_path)
                mp4_name = f"recording_{ts}.mp4"
                mp4_path = os.path.join(RECORDINGS_DIR, mp4_name)
                log("Converting to MP4...", "log-info")
                try:
                    subprocess.run(["ffmpeg", "-y", "-i", webm_path, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-movflags", "+faststart", mp4_path], capture_output=True, timeout=120)
                    if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                        try: os.remove(webm_path)
                        except: pass
                        agent_state["video_file"] = mp4_name
                        log(f"Recording: {mp4_name}", "log-action")
                    else:
                        agent_state["video_file"] = f"recording_{ts}.webm"
                except FileNotFoundError:
                    agent_state["video_file"] = f"recording_{ts}.webm"
                    log("ffmpeg not found — saved as webm", "log-error")
                except: agent_state["video_file"] = f"recording_{ts}.webm"
            else:
                agent_state["video_file"] = None
        except: agent_state["video_file"] = None
        log("Agent finished.", "log-done")


def run_in_thread(email, password, max_steps):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_agent_async(email, password, max_steps))
    loop.close()


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/start", methods=["POST"])
def api_start():
    if agent_state["running"]:
        return jsonify({"error": "Agent is already running"}), 400
    data = request.json
    email = data.get("email", "testqa.delhi21@gmail.com")
    password = data.get("password", "Test@12345")
    max_steps = data.get("max_steps", 40)
    thread = threading.Thread(target=run_in_thread, args=(email, password, max_steps), daemon=True)
    thread.start()
    time.sleep(2)
    return jsonify({"status": "started", "email": agent_state.get("test_email", ""), "app_name": agent_state.get("app_name", "")})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    agent_state["running"] = False
    return jsonify({"status": "stopping"})


@app.route("/api/status")
def api_status():
    al = agent_state.get("report") or []
    return jsonify({
        "running": agent_state["running"],
        "current_step": agent_state["current_step"],
        "current_stage": agent_state.get("current_stage", ""),
        "logs": agent_state["logs"],
        "screenshots": agent_state["screenshots"],
        "success_count": sum(1 for a in al if a.get("result") == "success"),
        "fail_count": sum(1 for a in al if "failed" in str(a.get("result", ""))),
        "test_email": agent_state.get("test_email", ""),
        "app_name": agent_state.get("app_name", ""),
        "video_file": agent_state.get("video_file"),
    })


@app.route("/screenshot/<filename>")
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOT_DIR, filename)


@app.route("/screenshot/live")
def serve_live():
    ss = agent_state.get("screenshots", [])
    if ss:
        return send_from_directory(SCREENSHOT_DIR, ss[-1])
    return "", 204


@app.route("/recording/<filename>")
def serve_recording(filename):
    return send_from_directory(RECORDINGS_DIR, filename)


if __name__ == "__main__":
    print(f"\n  INR Trial Agent Dashboard: http://0.0.0.0:8080\n")
    app.run(host="0.0.0.0", port=8080, debug=False)
