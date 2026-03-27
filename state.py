# state.py
from dataclasses import dataclass, field
from typing import Dict, Optional, List

@dataclass
class AgentState:
    goal: str
    url: Optional[str] = None

    html: Optional[str] = None
    headlines: Optional[List[str]] = None
    summary: Optional[str] = None

    scrape_strategy: Optional[str] = None   # "static" | "selenium"
    extract_strategy: Optional[str] = None  # "rule" | "llm"

    last_action: Optional[str] = None

    last_action: Optional[str] = None
    last_critic_feedback: Optional[str] = None
    # ✅ NEW: implicit execution history
    attempts: Dict[str, int] = field(default_factory=lambda: {
        "fetch_static": 0,
        "fetch_selenium": 0,
        "extract_rule": 0,
        "extract_llm": 0,
        "summarize": 0,
    })

    errors: List[dict] = field(default_factory=list)
    
    def add_error(self, action: str, message: str, recoverable: bool = True):
        self.errors.append({
            "action": action,
            "message": message,
            "recoverable": recoverable
        })



    @classmethod
    def from_dict(cls, data: dict):
        state = cls(
            url=data.get("url"),
            task=data.get("task")
        )
        state.html = data.get("html")
        state.headlines = data.get("headlines")
        state.summary = data.get("summary")
        state.errors = data.get("errors", [])
        state.attempts = data.get("attempts", {
            "fetch_static": 0,
            "fetch_selenium": 0,
            "extract_rule": 0,
            "extract_llm": 0,
            "summarize": 0,
        })
        return state

    def to_dict(self):
        return {
            "url": self.url,
            "task": self.task,
            "html": self.html,
            "headlines": self.headlines,
            "summary": self.summary,
            "errors": self.errors,
            "attempts": self.attempts,
        }

