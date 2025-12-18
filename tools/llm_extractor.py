import json
from pydantic import ValidationError
from llm.schema import HeadlineExtraction
from tools.llm_prompts import HEADLINE_EXTRACTION_PROMPT

def extract_headlines_with_llm(
    text: str,
    llm,
    max_retries: int = 2
) -> list[str]:

    last_error = None

    for attempt in range(max_retries + 1):
        prompt = HEADLINE_EXTRACTION_PROMPT.format(text=text)

        raw = llm.ask(prompt)

        try:
            data = json.loads(raw)

            data["headlines"] = data["headlines"][:10]

            validated = HeadlineExtraction(**data)
            return validated.headlines

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)

            # self-correcting retry
            prompt = f"""
The previous output was INVALID.

Error:
{e}

Please retry and return VALID JSON ONLY
following this schema:
{{
  "headlines": ["...", "..."]
}}

TEXT:
{text}
"""

    raise RuntimeError(f"LLM extraction failed after retries: {last_error}")
