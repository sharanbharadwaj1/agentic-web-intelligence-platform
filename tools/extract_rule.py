# tools/extract_rule.py
from bs4 import BeautifulSoup

class ExtractRuleTool:
    def run(self, state):
        soup = BeautifulSoup(state.html, "html.parser")
        headlines = [h.text.strip() for h in soup.select("h1,h2")]

        if not headlines:
            raise RuntimeError("No headlines found")

        state.headlines = headlines[:10]
        state.extract_strategy = "rule"
