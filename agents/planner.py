# agents/planner.py
class PlannerAgent:
    def decide(self, state):
        # Need HTML
        if state.html is None:
            return {"action": "fetch_static", "reason": "Try static scrape first"}

        # If static failed badly, try selenium
        if state.html and "Access Denied" in state.html:
            return {"action": "fetch_selenium", "reason": "Static blocked"}

        # Need headlines
        if state.headlines is None:
            return {"action": "extract_rule", "reason": "Try rule-based extraction"}

        # Need summary
        if state.summary is None:
            return {"action": "summarize", "reason": "Generate summary"}

        return {"action": "finish", "reason": "Goal reached"}
