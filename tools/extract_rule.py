# tools/extract_rule.py
from asyncio.log import logger
from bs4 import BeautifulSoup
# from tools.extract_llm import ExtractLLMTool
# extractllm = ExtractLLMTool()
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractRuleTool:
    def extract(self, state):
        print("Reaching rule-based extraction step...")
        if not state.html:
            raise RuntimeError("No HTML available for rule-based extraction")

        soup = BeautifulSoup(state.html, "html.parser")

        headlines = [
            h.get_text(strip=True)
            for h in soup.select("h1,h2,h3")
            if len(h.get_text(strip=True)) > 15
        ]

        if not headlines:
            raise RuntimeError("No headlines found (rule-based)")

        state.headlines = headlines[:10]
        state.extract_strategy = "rule"
        return state.headlines
    
    def run(self, state):
        headlines = self.extract(state)
        if headlines:
            print(f"Extracted headlines using rule-based extraction: {headlines}")

        state.headlines = headlines
        state.extract_strategy = "rule"

        return {
            "headlines": headlines,
            "extract_strategy": "rule"
        }



