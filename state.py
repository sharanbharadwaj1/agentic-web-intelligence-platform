# state.py
from dataclasses import dataclass, field

@dataclass
class AgentState:
    goal: str
    url: str | None = None

    html: str | None = None
    headlines: list[str] | None = None
    summary: str | None = None

    scrape_strategy: str | None = None  # "static" | "selenium"
    extract_strategy: str | None = None  # "rule" | "llm"

    last_action: str | None = None
    errors: list[str] = field(default_factory=list)
