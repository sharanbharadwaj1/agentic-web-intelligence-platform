# tools/extract.py
from bs4 import BeautifulSoup

class ExtractTool:
    def run(self, state):
        soup = BeautifulSoup(state.html, "html.parser")
        state.headlines = [h.text for h in soup.select("h1,h2")][:10]