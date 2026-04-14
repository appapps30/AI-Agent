"""
Stage Planner — Stage-aware LLM planner that uses flow context + RAG
knowledge to decide the next action at each stage.
"""
import json
import time
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, MAX_TOKENS

SYSTEM_PROMPT = """You are an autonomous QA testing agent navigating a multi-step web application flow.
You receive: the current stage, stage-specific instructions, relevant page elements, past actions, RAG knowledge context, and optionally a USER GOAL.

When a USER GOAL is provided, it is your PRIMARY objective. Adapt your actions to fulfill the goal. The goal takes priority over default stage instructions when they conflict.

Decide the SINGLE next best action.

## Available Actions (JSON format)

1. **click** — {"action": "click", "selector": "CSS selector", "description": "why"}
2. **fill** — {"action": "fill", "selector": "CSS selector", "value": "text", "description": "why"}
3. **select** — {"action": "select", "selector": "CSS selector", "value": "option", "description": "why"}
4. **navigate** — {"action": "navigate", "url": "https://...", "description": "why"}
5. **scroll** — {"action": "scroll", "direction": "down|up", "description": "why"}
6. **wait** — {"action": "wait", "duration": 2000, "description": "why"}
7. **press_enter** — {"action": "press_enter", "description": "why"}
8. **need_otp** — {"action": "need_otp", "description": "OTP input found, need to fetch code from email"}
9. **signup_done** — {"action": "signup_done", "description": "signup submitted, need email verification"}
10. **done** — {"action": "done", "description": "summary of what was accomplished"}

## Rules
- If a USER GOAL is provided, follow it as your primary directive
- Follow the stage instructions precisely (unless the goal overrides them)
- Use the EXACT email and password provided in stage context
- For OTP: return "need_otp" when you see an OTP/verification code input — the system handles fetching
- Do NOT navigate away from the target site in the main browser

## SELF-HEALING (CRITICAL)
- NEVER repeat a selector that already failed. Check your past actions — if a selector failed, use a DIFFERENT one.
- If #id fails, try: input[type="..."], input[placeholder*="..."], input[name="..."], or look at the page elements list for the actual selector.
- If a click fails, try: text-based selector, class-based selector, or scroll first then retry.
- If stuck on the same step for 3+ turns, try a completely different approach (scroll, wait, click something else).
- Look at the "Page Elements" section — it shows ACTUAL selectors that exist on the page. Use those.
- If an error message is visible on the page (e.g., "Password is required"), it tells you what field needs to be filled.

Respond ONLY with the JSON action object."""


class StagePlanner:
    def __init__(self, goal: str = ""):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.goal = goal

    def decide_action(
        self,
        current_url: str,
        stage_prompt: str,
        elements_summary: str,
        rag_context: str,
        past_actions: list[dict],
        step: int,
    ) -> dict:
        """Ask the LLM to decide the next action with full stage context."""

        # Build past actions summary (include description + selector so LLM knows what was already done)
        past_lines = ""
        if past_actions:
            past_lines = "\n## Past Actions\n"
            for a in past_actions[-8:]:
                desc = a.get('description', '')
                sel = a.get('selector', '')
                detail = f" [{desc}]" if desc else ""
                sel_info = f" (selector: {sel})" if sel else ""
                past_lines += f"- Step {a.get('step')}: {a.get('action_type')}{detail}{sel_info} -> {a.get('result', '?')}\n"

        # Build goal section
        goal_section = ""
        if self.goal:
            goal_section = f"\n## USER GOAL\n**\"{self.goal}\"**\nAdapt your actions to achieve this goal. But ALWAYS fill required form fields (email, name, etc.) before clicking submit buttons.\n"

        user_message = f"""## Current State
- **URL**: {current_url}
- **Step**: {step}
{goal_section}
{stage_prompt}

{elements_summary}

{rag_context}

{past_lines}

What is the single best next action?"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            action = json.loads(text)
        except json.JSONDecodeError:
            action = {"action": "done", "description": f"Unparseable: {text[:200]}"}

        return action
