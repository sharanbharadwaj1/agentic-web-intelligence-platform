import json
import re
from bs4 import BeautifulSoup

MAX_CHARS = 8000
SCRIPT_JSON_THRESHOLD = 2000  # chars


def prepare_llm_text(html: str) -> str:
    """
    Normalize scraped content for LLM consumption.
    Handles:
    - Static HTML
    - JS-rendered DOM
    - Embedded JSON SPA state
    """

    soup = BeautifulSoup(html, "html.parser")

    # --- 1. Measure content makeup ---
    visible_text = soup.get_text(strip=True)
    script_text = "".join(s.get_text() for s in soup.find_all("script"))

    # Heuristic: SPA / JS-heavy
    is_js_heavy = len(script_text) > len(visible_text)

    # --- 2. Try JSON extraction if JS-heavy ---
    if is_js_heavy:
        json_candidates = []

        for script in soup.find_all("script"):
            text = script.get_text()

            if not text or len(text) < SCRIPT_JSON_THRESHOLD:
                continue

            # Try to locate JSON objects
            matches = re.findall(r"\{.*\}", text, flags=re.DOTALL)
            for m in matches:
                try:
                    parsed = json.loads(m)
                    json_candidates.append(parsed)
                except Exception:
                    continue

        # Extract headline-like fields
        extracted = []

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in {"hl", "headline", "title"} and isinstance(v, str):
                        extracted.append(v)
                    walk(v)
            elif isinstance(obj, list):
                for x in obj:
                    walk(x)

        for jc in json_candidates:
            walk(jc)

        # If JSON yielded useful content, return it
        if len(extracted) >= 3:
            text = "\n".join(dict.fromkeys(extracted))
            return text[:MAX_CHARS]

    # --- 3. Fallback: clean visible HTML ---
    for tag in soup(["script", "style", "noscript", "header", "footer", "aside"]):
        tag.decompose()

    clean_text = soup.get_text(separator="\n", strip=True)

    return clean_text[:MAX_CHARS]





# from bs4 import BeautifulSoup

# def prepare_llm_text(html: str, max_chars: int = 8000) -> str:
#     soup = BeautifulSoup(html, "html.parser")

#     for tag in soup(["script", "style", "noscript", "header", "footer", "aside"]):
#         tag.decompose()

#     text = soup.get_text(separator="\n", strip=True)
#     return text[:max_chars]
