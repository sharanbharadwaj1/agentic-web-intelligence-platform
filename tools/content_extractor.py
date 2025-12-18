from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

def fetch_articles(headlines: list[dict], timeout: int = 10, max_chars: int = 4000):
    """
    Fetch article content for each headline.
    Returns list of dicts: {title, url, content}
    """

    articles = []

    headers = {"User-Agent": "Mozilla/5.0"}

    for item in headlines:
        url = item.get("url")
        title = item.get("title")

        if not url:
            continue

        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            html = resp.text
        except Exception:
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "noscript", "header", "footer", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        if len(text) > max_chars:
            text = text[:max_chars]

        articles.append({
            "title": title,
            "url": url,
            "content": text
        })

    return articles


def extract_headlines(html: str, base_url: str | None = None, limit: int = 10):
    """
    Extract visible headlines from HTML.
    Returns a list of dicts: [{title, url}]
    """

    soup = BeautifulSoup(html, "html.parser")

    headlines = []
    seen = set()

    # 1. Prefer semantic headline tags
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if not text or len(text) < 15:
            continue

        link = tag.find("a")
        href = link.get("href") if link else None

        if href and base_url:
            href = urljoin(base_url, href)

        key = (text, href)
        if key not in seen:
            seen.add(key)
            headlines.append({"title": text, "url": href})

        if len(headlines) >= limit:
            return headlines

    # 2. Fallback: anchor-heavy news sites
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href")

        if not text or not href:
            continue

        if len(text) < 20 or len(text) > 120:
            continue

        if base_url:
            href = urljoin(base_url, href)

        key = (text, href)
        if key not in seen:
            seen.add(key)
            headlines.append({"title": text, "url": href})

        if len(headlines) >= limit:
            break

    return headlines
