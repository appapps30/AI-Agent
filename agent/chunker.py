"""
Chunker module — Splits HTML DOM into smaller, meaningful chunks for embedding.
"""
import json
from bs4 import BeautifulSoup
from config import MAX_CHUNK_CHARS


def chunk_interactive_elements(interactive_json: str) -> list[dict]:
    """
    Takes the JSON string of interactive elements from the browser
    and groups them into chunks under MAX_CHUNK_CHARS.
    Each chunk is a dict with 'text' (for embedding) and 'elements' (raw data).
    """
    elements = json.loads(interactive_json)
    chunks = []
    current_chunk_text = ""
    current_chunk_elements = []

    for el in elements:
        el_text = _element_to_text(el)
        if len(current_chunk_text) + len(el_text) > MAX_CHUNK_CHARS and current_chunk_elements:
            chunks.append({
                "text": current_chunk_text.strip(),
                "elements": current_chunk_elements,
            })
            current_chunk_text = ""
            current_chunk_elements = []

        current_chunk_text += el_text + "\n"
        current_chunk_elements.append(el)

    if current_chunk_elements:
        chunks.append({
            "text": current_chunk_text.strip(),
            "elements": current_chunk_elements,
        })

    return chunks


def chunk_full_html(html: str) -> list[dict]:
    """
    Splits full HTML by top-level semantic sections (header, main, nav, footer, section, div).
    Falls back to splitting by character limit.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove script/style noise
    for tag in soup.find_all(["script", "style", "noscript", "svg"]):
        tag.decompose()

    sections = soup.find_all(["header", "nav", "main", "section", "article", "footer", "form"])

    if not sections:
        sections = soup.find_all("div", recursive=False)

    chunks = []
    for sec in sections:
        text = sec.get_text(separator=" ", strip=True)
        if not text:
            continue
        # Split large sections further
        if len(text) > MAX_CHUNK_CHARS:
            for i in range(0, len(text), MAX_CHUNK_CHARS):
                chunks.append({"text": text[i:i + MAX_CHUNK_CHARS], "html_tag": sec.name})
        else:
            chunks.append({"text": text, "html_tag": sec.name})

    return chunks


def _element_to_text(el: dict) -> str:
    """Convert a single interactive element dict to a searchable text line."""
    tag = el.get("tag", "")
    attrs = el.get("attrs", {})
    text = el.get("text", "")
    selector = el.get("selector", "")

    parts = [f"[{tag}]"]
    if attrs.get("type"):
        parts.append(f"type={attrs['type']}")
    if attrs.get("placeholder"):
        parts.append(f"placeholder=\"{attrs['placeholder']}\"")
    if attrs.get("aria-label"):
        parts.append(f"aria-label=\"{attrs['aria-label']}\"")
    if attrs.get("href"):
        parts.append(f"href={attrs['href'][:80]}")
    if attrs.get("name"):
        parts.append(f"name={attrs['name']}")
    if text:
        parts.append(f"text=\"{text[:100]}\"")
    parts.append(f"selector=\"{selector}\"")
    return " ".join(parts)
