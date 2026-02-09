# tools/fetch_static.py
from asyncio.log import logger
import requests

class FetchStaticTool:
    def run(self, state):
        print(f"Fetching static content from {state.url}")
        # logger.info(f"Fetching static content from {state.url}")
        r = requests.get(state.url, timeout=10)
        r.raise_for_status()
        state.html = r.text
        print(f"Fetched {len(state.html)} characters of HTML")
        # print(f"Fetched HTML content : {state.html[:5000]}")
        state.scrape_strategy = "static"
