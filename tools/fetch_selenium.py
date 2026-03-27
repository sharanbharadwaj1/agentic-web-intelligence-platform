# tools/fetch_selenium.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class FetchSeleniumTool:
   



    def fetch_selenium(self, state) :
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        driver.get(state.url)

        time.sleep(5)  # allow JS to load
        try:
            state.html = driver.page_source
            driver.quit()
            html_lower = state.html.lower()
            for x in ["access denied", "bot protection", "captcha", "cloudflare", "verify you are human"]:
                if x in html_lower:
                    logger.info(f"Bot protection detected due to presence of '{x}' in HTML.")
                    raise ConnectionRefusedError("Bot protection detected!!")
        #     if (
        #     "access denied" in html_lower
        #     or "bot protection" in html_lower
        #     or "captcha" in html_lower
        #     or "cloudflare" in html_lower
        #     or "verify you are human" in html_lower
        # ):
                driver.quit()
                raise RuntimeError("Selenium fetch blocked by bot protection")
        except:
            raise ConnectionRefusedError("Bot protection detected!!")
                
        state.scrape_strategy = "selenium"

    def run(self, state):
        html = self.fetch_selenium(state)

        state.html = html
        state.scrape_strategy = "static"

        return {
            "html": html,
            "scrape_strategy": "selenium"
        }

