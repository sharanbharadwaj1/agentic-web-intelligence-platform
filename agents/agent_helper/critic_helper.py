def looks_like_real_headlines(headlines: list[str]) -> bool:
    if not headlines or len(headlines) < 3:
        return False

    bad_patterns = [
        "popular",
        "top stories",
        "trending",
        "recommended",
        "latest news",
    ]

    bad_count = 0
    for h in headlines:
        h_low = h.lower()
        if any(p in h_low for p in bad_patterns):
            bad_count += 1

    # If most headlines are generic → junk
    return bad_count < len(headlines) / 2
