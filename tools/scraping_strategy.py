from bs4 import BeautifulSoup

class ScrapingStrategyRouter:
    def __init__(self, static_scraper, selenium_scraper):
        self.static = static_scraper
        self.selenium = selenium_scraper

    def is_static_html(self, html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")

        text_len = len(soup.get_text(strip=True))
        script_len = sum(len(s.get_text()) for s in soup.find_all("script"))

        # Heuristics
        if script_len > text_len * 2:
            return False

        if soup.find("article"):
            return True

        headings = soup.find_all(["h1", "h2"])
        if len(headings) >= 5:
            return True

        return False

    def fetch(self, url: str):
        html = self.static.fetch_raw(url)

        if self.is_static_html(html):
            print(f"[ScrapingStrategy] Using static scraper for {url}")
            html = self.web.fetch(url)

            return html
        else:
            html = self.selenium.fetch(url)
            return html