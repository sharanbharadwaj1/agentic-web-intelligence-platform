# tools/fetch_static.py
from asyncio.log import logger
import requests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FetchStaticTool:
    def fetch(self, state):
        logger.info(f"Fetching static content from {state.url}")
        # logger.info(f"Fetching static content from {state.url}")
        r = requests.get(state.url, timeout=10)
        r.raise_for_status()
        state.html = r.text
        logger.info(f"Fetched {len(state.html)} characters of HTML")
        # logger.info(f"Fetched HTML content : {state.html[:5000]}")
        state.scrape_strategy = "static"
        return r.text

    def run(self, state):
        html = self.fetch(state)

        state.html = html
        state.scrape_strategy = "static"

        return {
            "html": html,
            "scrape_strategy": "static"
        }

    
