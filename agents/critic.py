# agents/critic.py
class CriticAgent:
    def validate(self, state):
        if state.last_action == "extract_rule" and not state.headlines:
            return False, "RULE_EXTRACTION_FAILED"

        if state.last_action == "fetch_static" and state.html and "Access Denied" in state.html:
            return False, "STATIC_BLOCKED"

        return True, "OK"
