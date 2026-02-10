from llm.config_loader import Config


def looks_blocked(html: str) -> bool:
    try:
        if not html:
            return True

        html_low = html.lower()
        block_markers = [
            "access denied",
            "forbidden",
            "captcha",
            "cloudflare",
            "akamai",
            "blocked",
            "verify you are human",
            "bot detection",
        ]
        return any(m in html_low for m in block_markers)
    except:
        markers = Config.load()["scraping"]["block_markers"]
        html_low = html.lower()
        return any(m in html_low for m in markers)

 