# tools/fetch_static.py
import requests

class FetchStaticTool:
    def run(self, state):
        r = requests.get(state.url, timeout=10)
        r.raise_for_status()
        state.html = r.text
        state.scrape_strategy = "static"
