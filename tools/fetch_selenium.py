# tools/fetch_selenium.py
from selenium import webdriver

class FetchSeleniumTool:
    def run(self, state):
        driver = webdriver.Chrome()
        driver.get(state.url)
        state.html = driver.page_source
        driver.quit()
        state.scrape_strategy = "selenium"
