"""
Retriever module — Queries vector store for relevant elements and enriches
results with past action patterns.
"""
import json
from agent.vector_store import VectorStore


class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.action_history: list[dict] = []  # past actions taken by the agent

    def record_action(self, action: dict):
        """Record an action that was executed, for pattern matching."""
        self.action_history.append(action)

    def retrieve(self, query: str, top_k: int = 10) -> dict:
        """
        Retrieve relevant elements from vector store and combine
        with past action patterns for LLM context.
        """
        matches = self.vector_store.search(query, top_k=top_k)

        # Collect all interactive elements from matching chunks
        all_elements = []
        for match in matches:
            all_elements.extend(match.get("elements", []))

        # Deduplicate by selector
        seen_selectors = set()
        unique_elements = []
        for el in all_elements:
            sel = el.get("selector", "")
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                unique_elements.append(el)

        return {
            "relevant_elements": unique_elements,
            "matched_chunks": [m["text"] for m in matches[:5]],
            "past_actions": self.action_history[-10:],  # last 10 actions
        }

    def get_context_summary(self, query: str) -> str:
        """Build a text summary for the LLM planner."""
        data = self.retrieve(query)

        lines = ["## Relevant Interactive Elements on Page\n"]
        for el in data["relevant_elements"][:20]:
            tag = el.get("tag", "?")
            text = el.get("text", "")[:80]
            selector = el.get("selector", "")
            attrs = el.get("attrs", {})
            desc = f"- <{tag}> text=\"{text}\" selector=\"{selector}\""
            if attrs.get("href"):
                desc += f" href=\"{attrs['href'][:60]}\""
            if attrs.get("type"):
                desc += f" type=\"{attrs['type']}\""
            if attrs.get("placeholder"):
                desc += f" placeholder=\"{attrs['placeholder']}\""
            if attrs.get("name"):
                desc += f" name=\"{attrs['name']}\""
            lines.append(desc)

        if data["past_actions"]:
            lines.append("\n## Past Actions Taken\n")
            for i, act in enumerate(data["past_actions"]):
                lines.append(f"{i+1}. {act.get('action_type', '?')}: {act.get('description', '?')} "
                             f"-> selector=\"{act.get('selector', '?')}\" result={act.get('result', '?')}")

        return "\n".join(lines)
