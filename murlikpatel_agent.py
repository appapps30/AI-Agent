#!/usr/bin/env python3
"""
Murlikpatel Autonomous QA Agent — End-to-end testing of the app creation flow
on the Murlikpatel App Builder platform (https://murlikpatel.myapparea.com).

Architecture:
  Dual Browser (two tabs) -> DOM Extraction -> Chunking -> Embeddings ->
  Vector DB -> Stage Detection -> RAG Knowledge -> LLM Decides ->
  Self-Healing Execute -> Repeat

Usage:
  python3 murlikpatel_agent.py
  python3 murlikpatel_agent.py --app-name "MyApp" --max-steps 40
  python3 murlikpatel_agent.py --email "user@example.com" --password "pass123"
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

from config import MAX_STEPS, SCREENSHOT_DIR
from agent.dual_browser import DualBrowser
from agent.chunker import chunk_interactive_elements
from agent.embedder import Embedder
from agent.vector_store import VectorStore
from agent.retriever import Retriever
from agent.stage_planner import StagePlanner
from agent.self_healing_executor import SelfHealingExecutor
from agent.rag_knowledge import RAGKnowledge
from agent.murlikpatel_orchestrator import MurlikpatelOrchestrator

# --- Logging Setup ---
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_filename = os.path.join(LOGS_DIR, f"murlikpatel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger = logging.getLogger("murlikpatel_agent")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


BASE_URL = "https://murlikpatel.myapparea.com"


def cleanup_screenshots():
    """Delete old screenshots before a new run."""
    if os.path.exists(SCREENSHOT_DIR):
        for f in glob.glob(os.path.join(SCREENSHOT_DIR, "*.png")):
            try:
                os.remove(f)
            except Exception:
                pass
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


async def run_murlikpatel_agent(
    app_name: str = None,
    max_steps: int = None,
    email: str = None,
    password: str = None,
):
    max_steps = max_steps or MAX_STEPS
    cleanup_screenshots()

    # --- Initialize orchestrator with credentials from RAG ---
    orchestrator = MurlikpatelOrchestrator(
        app_name=app_name,
        email=email or "rakesh@appypiellp.com",
        password=password or "Test@12345",
    )

    logger.info(f"\n{'='*60}")
    logger.info(f"  MURLIKPATEL AUTONOMOUS QA AGENT")
    logger.info(f"  Platform: {BASE_URL}")
    logger.info(f"  App Name: {orchestrator.app_name}")
    logger.info(f"  Email:    {orchestrator.email}")
    logger.info(f"  Password: {orchestrator.password}")
    logger.info(f"  Steps:    {max_steps}")
    logger.info(f"  Log:      {log_filename}")
    logger.info(f"{'='*60}\n")

    # --- Initialize components ---
    logger.info("[init] Launching dual browser (two tabs)...")
    browser = DualBrowser()
    await browser.launch()

    logger.info("[init] Loading embedding model + RAG knowledge...")
    embedder = Embedder()
    page_vector_store = VectorStore(embedder)
    retriever = Retriever(page_vector_store)
    rag_knowledge = RAGKnowledge(embedder)
    rag_knowledge.load_knowledge_base()

    planner = StagePlanner()
    executor = SelfHealingExecutor(browser.main_page)

    # --- Navigate to platform ---
    logger.info(f"\n[step 0] Navigating to {BASE_URL}")
    await browser.main_goto(BASE_URL)

    action_log = []
    login_submit_count = 0  # Track how many times we've submitted login

    try:
        for step in range(1, max_steps + 1):
            # --- Page recovery & wait ---
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

            # Keep executor in sync with current main page
            executor.page = browser.main_page

            # --- Screenshot ---
            await browser.main_screenshot(step)

            # --- Extract DOM ---
            interactive_json = await browser.get_main_interactive_elements()

            # --- Get page text ---
            page_text = ""
            try:
                page_text = await browser.main_page.evaluate(
                    "() => document.body.innerText.substring(0, 2000)"
                )
            except Exception:
                pass

            # --- Search for "AppyPie" / "Appy Pie" on this page ---
            page_html = ""
            try:
                page_html = await browser.main_page.evaluate(
                    "() => document.documentElement.outerHTML.substring(0, 50000)"
                )
            except Exception:
                pass
            search_hit = orchestrator.search_appypie(current_url, page_text, page_html)
            if search_hit:
                logger.info(f"  *** FOUND 'AppyPie'/'Appy Pie' on {current_url} ({search_hit['count']} occurrences) ***")
                ss_path = await browser.main_screenshot(step, "appypie_match")
                logger.info(f"  Screenshot saved: {ss_path}")

            # --- Detect stage ---
            stage = orchestrator.detect_stage(current_url, page_text)
            progress = orchestrator.get_progress_summary()

            logger.info(f"\n{'—'*55}")
            logger.info(f"[step {step}] {progress}")
            logger.info(f"  URL: {current_url}")

            # --- Login stuck detection ---
            if stage == "login" and login_submit_count >= 2:
                logger.info("  Login submitted multiple times but still on login page.")
                logger.info("  Attempting direct navigation to dashboard...")
                try:
                    await browser.main_page.goto(
                        f"{BASE_URL}/user",
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )
                    await asyncio.sleep(3)
                    new_url = await browser.main_url()
                    if "/user" in new_url or "/dashboard" in new_url:
                        logger.info(f"  Dashboard reached: {new_url}")
                        login_submit_count = 0
                        continue
                    else:
                        logger.info(f"  Still redirected to: {new_url} — credentials may be wrong")
                except Exception as e:
                    logger.debug(f"  Direct nav failed: {str(e)[:100]}")
                login_submit_count = 0  # Reset to avoid infinite nav loop

            # --- Chunk + embed + store page elements ---
            chunks = chunk_interactive_elements(interactive_json)
            logger.debug(f"  Chunks created: {len(chunks)}")
            page_vector_store.reset()
            page_vector_store.store_chunks(chunks)

            # --- Build context for LLM ---
            elements_summary = retriever.get_context_summary(
                f"interactive elements for {stage}"
            )
            stage_prompt = orchestrator.get_stage_prompt()
            rag_context = rag_knowledge.query(
                f"{stage} {current_url} next action murlikpatel"
            )

            logger.debug(f"  Stage prompt:\n{stage_prompt[:300]}")
            logger.debug(f"  Elements:\n{elements_summary[:300]}")
            logger.debug(f"  RAG context:\n{rag_context[:300]}")

            # --- Ask LLM for next action ---
            logger.info(f"  Asking LLM (stage: {stage})...")
            action = planner.decide_action(
                current_url, stage_prompt, elements_summary,
                rag_context, action_log, step
            )
            action_type = action.get("action", "unknown")
            description = action.get("description", "")
            logger.info(f"  -> {action_type}: {description}")

            # --- Handle DONE ---
            if action_type == "done":
                logger.info(f"\n  DONE: {description}")
                action_log.append({
                    "step": step, "action_type": "done",
                    "description": description, "result": "completed"
                })
                await browser.main_screenshot(step, "final")
                break

            # --- Handle popups/modals ---
            if action_type == "dismiss_popup":
                try:
                    await browser.main_page.keyboard.press("Escape")
                    logger.info("  Dismissed popup with Escape")
                except Exception:
                    pass
                action_log.append({
                    "step": step, "action_type": "dismiss_popup",
                    "description": description, "result": "success"
                })
                continue

            # --- Execute action via self-healing executor ---
            result = await executor.execute(action)
            success = result["success"]
            msg = result["message"]
            status = "OK" if success else "FAIL"
            logger.info(f"  [{status}] {msg}")

            # Track login submit attempts
            if success and action_type == "click" and "submitme" in str(action.get("selector", "")).lower():
                login_submit_count += 1
                logger.debug(f"  Login submit count: {login_submit_count}")

            if not success:
                logger.debug(f"  Failed action details: {json.dumps(action)}")

            action_log.append({
                "step": step,
                "action_type": action_type,
                "description": description,
                "selector": action.get("selector", ""),
                "value": action.get("value", ""),
                "url": current_url,
                "stage": stage,
                "result": "success" if success else f"failed: {msg}",
            })

            await asyncio.sleep(1)

        else:
            logger.info(f"\n  Reached max steps ({max_steps})")

    except Exception as e:
        logger.error(f"\n  AGENT ERROR: {str(e)[:300]}")
        action_log.append({
            "step": 0, "action_type": "error",
            "description": str(e)[:300], "result": "error"
        })

    finally:
        # --- Crawl key pages to search for "AppyPie" / "Appy Pie" ---
        logger.info(f"\n{'='*55}")
        logger.info(f"  SEARCHING FOR 'AppyPie' / 'Appy Pie' ACROSS WEBSITE")
        logger.info(f"{'='*55}")

        crawl_pages = [
            f"{BASE_URL}",
            f"{BASE_URL}/login",
            f"{BASE_URL}/user",
            f"{BASE_URL}/appbuilder/creator-software/",
            f"{BASE_URL}/pricing",
            f"{BASE_URL}/about",
            f"{BASE_URL}/contact",
            f"{BASE_URL}/support",
            f"{BASE_URL}/features",
            f"{BASE_URL}/terms-of-use",
            f"{BASE_URL}/privacy-policy",
        ]

        try:
            for page_url in crawl_pages:
                if page_url in orchestrator.pages_scanned:
                    continue
                try:
                    logger.info(f"  [scan] {page_url}")
                    await browser.main_goto(page_url)
                    await asyncio.sleep(2)

                    crawl_text = ""
                    crawl_html = ""
                    try:
                        crawl_text = await browser.main_page.evaluate(
                            "() => document.body.innerText.substring(0, 10000)"
                        )
                        crawl_html = await browser.main_page.evaluate(
                            "() => document.documentElement.outerHTML.substring(0, 50000)"
                        )
                    except Exception:
                        pass

                    hit = orchestrator.search_appypie(page_url, crawl_text, crawl_html)
                    if hit:
                        logger.info(f"    *** FOUND 'AppyPie'/'Appy Pie' — {hit['count']} occurrences ***")
                        for occ in hit["occurrences"][:3]:
                            logger.info(f"      [{occ['type']}] [{occ.get('term', '')}] ...{occ['context'][:80]}...")
                        # Save screenshot for the matched page
                        page_label = page_url.rstrip("/").split("/")[-1] or "home"
                        scan_ss = await browser.main_screenshot(0, f"appypie_scan_{page_label}")
                        logger.info(f"    Screenshot saved: {scan_ss}")
                    else:
                        logger.info(f"    No 'AppyPie'/'Appy Pie' found")
                except Exception as e:
                    logger.debug(f"    Scan error: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"  Crawl error: {str(e)[:200]}")

        # --- Search Report ---
        search_report = orchestrator.get_search_report()
        logger.info(f"\n{'—'*55}")
        logger.info(f"  SEARCH REPORT: 'AppyPie' / 'Appy Pie'")
        logger.info(f"  Search terms:       {search_report['search_terms']}")
        logger.info(f"  Pages scanned:      {search_report['pages_scanned']}")
        logger.info(f"  Pages with matches: {search_report['pages_with_matches']}")
        logger.info(f"  Total occurrences:  {search_report['total_occurrences']}")
        if search_report["results"]:
            logger.info(f"  Matched pages:")
            for r in search_report["results"]:
                logger.info(f"    - {r['url']} ({r['count']} hits)")
        else:
            logger.info(f"  No 'AppyPie'/'Appy Pie' found anywhere on the website.")
        logger.info(f"{'—'*55}")

        # --- Generate Report ---
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
            "appypie_search": search_report,
        }

        report_path = os.path.join(os.path.dirname(__file__), "murlikpatel_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n  Report:  {report_path}")
        logger.info(f"  Log:     {log_filename}")
        logger.info(f"  Actions: {len(action_log)} ({successful} ok, {failed} failed)")
        logger.info(f"  Stages:  {' -> '.join(orchestrator.stage_history)}")

        video_path = await browser.close()
        if video_path:
            logger.info(f"  Video:   {video_path}")

        logger.info("\n  Agent finished.\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="Murlikpatel Autonomous QA Agent")
    parser.add_argument("--app-name", "-a", default=None, help="App name to create")
    parser.add_argument("--max-steps", "-n", type=int, default=35, help="Max steps")
    parser.add_argument("--email", "-e", default=None, help="Login email")
    parser.add_argument("--password", "-p", default=None, help="Login password")
    args = parser.parse_args()

    asyncio.run(run_murlikpatel_agent(
        app_name=args.app_name,
        max_steps=args.max_steps,
        email=args.email,
        password=args.password,
    ))


if __name__ == "__main__":
    main()
