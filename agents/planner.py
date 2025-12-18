# agents/planner.py
import json
import re
from typing import List, Optional
from llm.groq_client import GroqClient

# Deterministic fallback plan used when LLM is unavailable or returns unusable output.
FALLBACK_PLAN = [
    "Fetch the webpage at {url}",
    "Parse the HTML and extract the target data (headlines, titles, links, etc.)",
    "Store the extracted data in memory",
    "Summarize the stored data into a concise report",
    "Format and return the final report"
]

class PlannerAgent:
    def __init__(self, model_name: Optional[str] = None):
        """
        PlannerAgent uses GroqClient to decompose a URL-specific task into atomic steps.
        """
        self.llm = GroqClient(model_name) if model_name is None else GroqClient(model_name=model_name)

    # ---------- Helpers ----------
    def _looks_like_error(self, text: Optional[str]) -> bool:
        if not text:
            return True
        low = text.lower()
        markers = ["error", "exception", "quota", "not-available", "resourceexhausted", "model_not_found", "traceback", "[groq error]"]
        return any(m in low for m in markers)

    def _heuristic_parse_steps(self, text: str) -> List[str]:
        """
        Heuristic parser to extract actionable steps from plain text.
        - extracts numbered / bullet lines
        - falls back to sentence splitting
        """
        if not text:
            return []

        # split into lines and keep lines that look actionable
        lines = []
        for raw in text.splitlines():
            s = raw.strip()
            if not s:
                continue
            # remove leading list markers and "Step N:" prefixes
            s = re.sub(r'^\s*step\s*\d+\s*[:\-\)]\s*', '', s, flags=re.I)
            s = re.sub(r'^[\-\*\u2022\)\(\s\d\.]+', '', s)
            # skip short garbage lines
            if len(s) < 6:
                continue
            # make it a single action by truncating after semicolon if verbose
            s = s.split(';')[0].strip()
            lines.append(s)
        if len(lines) >= 2:
            return lines

        # fallback: sentence-split and keep first meaningful sentences
        sentences = re.split(r'(?<=[\.\?\!])\s+', text)
        steps = [s.strip() for s in sentences if len(s.strip()) > 10]
        return steps[:6]

    def _ensure_url_in_steps(self, url: str, steps: List[str]) -> List[str]:
        """
        Make sure the first step fetches the provided url. If not present, inject it.
        Also replace any {url} placeholder in steps with the real URL.
        """
        # replace placeholders
        steps = [s.replace("{url}", url) for s in steps]

        # detect if any step already explicitly fetches or navigates to the url
        url_present = any(("fetch " in s.lower() and url in s) or ("open " in s.lower() and url in s)
                          or ("visit " in s.lower() and url in s) for s in steps)
        # also accept step that mentions url implicitly (contains domain)
        domain = re.sub(r'^https?://', '', url).split('/')[0].lower()
        if not url_present:
            for s in steps:
                if domain in s.lower():
                    url_present = True
                    break

        if not url_present:
            # insert fetch as the first actionable step
            fetch_step = f"Fetch the webpage at {url}"
            steps.insert(0, fetch_step)
        return steps

    # ---------- Public API ----------
    def plan(self, url: str, task: str) -> List[str]:
        """
        Generate a list of atomic steps tailored to the given URL and task.
        Returns a list of short action strings.
        """
        # safety checks
        if not url or not task:
            return [s.format(url=url) for s in FALLBACK_PLAN]

        # Build the structured prompt
        prompt = f"""
You are an expert assistant that decomposes a user's URL-specific task into a short ordered
list of minimal, atomic, directly-executable steps. Each step must be one action (verb + object)
and must be specific to the provided URL when extraction is required.

INPUT:
URL: {url}
TASK: {task}

REQUIREMENTS:
- Return ONLY JSON in this exact shape: {{ "steps": ["step 1", "step 2", ...] }}
- Each step must be a single action and executable by an agent (verbs like: Fetch, Parse, Extract, Store, Summarize, Return).
- If the task requires scraping or data extraction, ensure the plan includes a step that fetches the provided URL.
- Do NOT include explanation text or notes — only the JSON object.

SPECIAL INSTRUCTIONS:

- You are planning steps for an automated agent.

- You MUST use ONLY the following step formats:

    1. Fetch <url>
    2. Extract headlines
    3. Summarize headlines into two sentences
    4. Return result

DO NOT invent new step types.
DO NOT include parsing, storing, or analysis steps.

"""

        schema = {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["steps"]
        }

        # Try structured call to the LLM
        try:
            response_text = self.llm.structured(prompt, schema=schema)
        except Exception as e:
            # LLM invocation failed; fall back
            response_text = f"[Groq Error] {e}"

        # If response looks like an error, try plain ask fallback
        if self._looks_like_error(response_text):
            try:
                plain_prompt = f"""
Decompose the following URL-aware task into short numbered steps (one action per line).

URL: {url}
TASK: {task}

Return only the steps, one per line.
"""
                plain_text = self.llm.ask(plain_prompt)
            except Exception:
                plain_text = ""
            steps = self._heuristic_parse_steps(plain_text)
            if not steps:
                # final fallback
                return [s.format(url=url) for s in FALLBACK_PLAN]
            steps = self._ensure_url_in_steps(url, steps)
            return steps

        # Try to parse the JSON returned by structured()
        try:
            parsed = json.loads(response_text)
            steps = parsed.get("steps") if isinstance(parsed, dict) else None
            if isinstance(steps, list) and steps:
                # normalize and ensure URL presence
                cleaned = [str(s).strip() for s in steps if str(s).strip()]
                cleaned = self._ensure_url_in_steps(url, cleaned)
                return cleaned
        except Exception:
            # not valid JSON — use heuristic parsing of raw text
            steps = self._heuristic_parse_steps(response_text)
            if steps:
                steps = self._ensure_url_in_steps(url, steps)
                return steps

        # As a final fallback, return deterministic plan with URL inserted
        return [s.format(url=url) for s in FALLBACK_PLAN]
