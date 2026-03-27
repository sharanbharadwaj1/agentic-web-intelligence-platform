# tools/extract_llm.py
from asyncio.log import logger
from tools.utils.headline_extraction_prompt import HEADLINE_EXTRACTION_PROMPT
from tools.utils.headline_extraction_schema import HEADLINE_EXTRACTION_SCHEMA
from llm.groq_client import GroqClient
import json
import re
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractLLMTool:
    def __init__(self, llm: GroqClient | None = None):
        self.llm = llm or GroqClient()

    def extract_llm(self, state):
        html = (state.html or "")[:8000]
        prompt = HEADLINE_EXTRACTION_PROMPT.format(html=html)

        try:
            raw = self.llm.structured(prompt, schema=HEADLINE_EXTRACTION_SCHEMA)
            logger.info(f"LLM raw output: {raw}")

            # --- sanitize markdown/code fences ---
            if isinstance(raw, str) and "```" in raw:
                raw = re.sub(r"```[a-zA-Z]*\n?", "", raw)
                raw = raw.replace("```", "").strip()

            # --- parse JSON ---
            if isinstance(raw, str):
                parsed = json.loads(raw)
            elif isinstance(raw, dict):
                parsed = raw
            else:
                raise RuntimeError(f"Unexpected LLM output type: {type(raw)}")

            headlines = parsed.get("headlines")
            if not headlines or not isinstance(headlines, list):
                raise RuntimeError("LLM returned no valid headlines")

            # --- mutate state (implicit execution) ---
            state.headlines = headlines[:10]
            state.extract_strategy = "llm"
            return state.headlines

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise RuntimeError(f"LLM extraction failed: {e}")
        
    def run(self, state):
        headlines = self.extract_llm(state)

        state.headlines = headlines
        state.extract_strategy = "llm"

        return {
            "headlines": headlines,
            "extract_strategy": "llm"
        }
