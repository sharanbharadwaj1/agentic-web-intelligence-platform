# import requests
# from bs4 import BeautifulSoup

# class WebScraper:
#     def __init__(self, timeout: int = 10):
#         self.timeout = timeout
#         self.headers = {
#             "User-Agent": "Mozilla/5.0 (AgentPlatform/1.0)"
#         }

#     def fetch(self, url: str) -> str:
#         """
#         Fetch raw HTML from a URL.
#         Used by automation (watchers) and executor.
#         """
#         resp = requests.get(url, headers=self.headers, timeout=self.timeout)
#         resp.raise_for_status()
#         return resp.text

#     def scrape_hackernews(self):
#         print("Scraping Hacker News...")
#         url = "https://lucassifoni.info/blog/miniscope-tiny-telescope/"
#         resp = requests.get(url, timeout=10)
#         soup = BeautifulSoup(resp.text, "html.parser")

#         links = soup.select(".titleline > a")
#         titles = [a.text for a in links][:10]
#         print(f"Scraped : {resp[:100]}")
#         print(f"Titles: {titles}")
#         return titles


# tools/web_scraper.py
# import requests

# class WebScraper:
#     def fetch(self, url: str) -> str:
#         resp = requests.get(
#             url,
#             headers={"User-Agent": "Mozilla/5.0"},
#             timeout=10
#         )
#         resp.raise_for_status()
#         return resp.text


# tools/web_scraper.py
import requests
from bs4 import BeautifulSoup

class WebScraper:
    def fetch_raw(self, url: str) -> str:
        headers = {"User-Agent": "Mozilla/5.0"}
        return requests.get(url, headers=headers, timeout=10).text

    def extract(self, url: str, html: str):
        soup = BeautifulSoup(html, "html.parser")
        return [h.get_text(strip=True) for h in soup.find_all("h2")[:10]]
    
    def fetch(self, url: str) -> str:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.text

