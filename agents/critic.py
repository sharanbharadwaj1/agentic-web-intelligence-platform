# agents/critic.py
from agents.agent_helper.critic_helper import looks_like_real_headlines


class CriticAgent:
    def validate(self, state):
        
        if state.last_action == "extract_rule" and not state.headlines:
            return False, "RULE_EXTRACTION_FAILED"

        if state.last_action == "fetch_static" and state.html and "Access Denied" in state.html:
            return False, "STATIC_BLOCKED"
        
        if (
            state.attempts["extract_rule"] > 2
            and state.headlines is None
        ):
            return False, "Stuck in rule-based extraction"
        
        if (
            state.last_action == "extract_llm"
            and state.attempts["extract_llm"] >= 2
            and not state.headlines
        ):
            return False, "LLM_EXTRACTION_FAILED_REPEATEDLY"
        
        if (
            state.last_action == "extract_llm"
            and state.attempts["extract_llm"] >= 1
            and not state.headlines
        ):
            return False, "LLM_OUTPUT_INVALID"
        
        if (
            state.last_action == "extract_rule"
            and state.scrape_strategy == "static"
            and state.headlines
            and not looks_like_real_headlines(state.headlines)
        ):
            return False, "STATIC_EXTRACTION_LOW_QUALITY"

        
        for err in state.errors:
            if err["action"] == "extract_llm" and not err["recoverable"]:
                return False, "NON_RECOVERABLE_LLM_FAILURE"





        return True, "OK"
