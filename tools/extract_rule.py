# tools/extract_rule.py
from asyncio.log import logger
from bs4 import BeautifulSoup
# from tools.extract_llm import ExtractLLMTool
# extractllm = ExtractLLMTool()

class ExtractRuleTool:
    def run(self, state):
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

# class ExtractRuleTool:
#     def run(self, state):
#         soup = BeautifulSoup(state.html, "html.parser")
#         while state.attempts["extract_rule"] < 3:
#             state.attempts["extract_rule"] += 1
#             headlines = [h.text.strip() for h in soup.select("h1,h2")]

#         if not headlines:
#             # raise RuntimeError("No headlines found")
#             if state.attempts["extract_rule"] > 2:  # only after 2 tries
#                 logger.warning(f"Retries is {state.attempts['extract_rule']} \n No headlines found with rule-based extraction, FALLING back to LLM-based extraction")
#                 headlines = extractllm.run(state)
#                 state.attempts["extract_llm"] += 1
#         state.headlines = headlines[:10]
#         state.extract_strategy = "llm" if state.attempts["extract_llm"] > 0 else "rule"
