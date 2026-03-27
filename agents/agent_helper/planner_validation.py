def validate_planner_output(parsed: dict) -> bool:
    return (
        isinstance(parsed, dict)
        and parsed.get("action") in {
            "fetch_static",
            "fetch_selenium",
    "extract_rule",
    "extract_llm",
            "summarize",
            "finish",
        }
        and isinstance(parsed.get("reason"), str)
    )
