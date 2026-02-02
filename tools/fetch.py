# tools/fetch.py
import requests

class FetchTool:
    def run(self, state):
        r = requests.get(state.url, timeout=10)
        r.raise_for_status()
        state.html = r.text