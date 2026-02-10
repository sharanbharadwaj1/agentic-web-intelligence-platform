from bs4 import BeautifulSoup

def looks_js_rendered(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")

    text_len = len(soup.get_text(strip=True))
    script_count = len(soup.find_all("script"))
    heading_count = len(soup.find_all(["h1", "h2", "h3"]))
    
    if script_count > 30 and heading_count < 5:
        return True

    if text_len < 500:
        return True

    return False
