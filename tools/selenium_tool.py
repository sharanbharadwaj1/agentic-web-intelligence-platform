
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

# class SeleniumTool:
#     def run(self):
#         options = Options()
#         options.add_argument("--headless")
#         driver = webdriver.Chrome(options=options)

#         driver.get("https://lucassifoni.info/blog/miniscope-tiny-telescope/")
#         title = driver.title
#         driver.quit()
#         return title


# tools/selenium_tool.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class SeleniumTool:
    def fetch(self, url: str) -> str:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        driver.get(url)

        time.sleep(5)  # allow JS to load

        html = driver.page_source
        driver.quit()
        return html
