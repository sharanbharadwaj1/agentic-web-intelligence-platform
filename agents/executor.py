# agents/executor.py
class ExecutorAgent:
    def __init__(self, registry):
        self.registry = registry

    def execute(self, action: str, state):
        """
        Execute a single action by looking up the tool in the registry
        and running it against the state.

        The tool:
          - is responsible for mutating `state` (e.g., state.html, state.headlines, state.summary).
          - may optionally return a value, which we pass back to the caller.
        """
        
        tool = self.registry.get(action)
        if tool is None:
            # Optional: record error on state if your AgentState has errors list
            if hasattr(state, "errors"):
                state.errors.append(f"unknown_action:{action}")
            raise ValueError(f"Unknown action: {action}")
        
        # ✅ increment attempt count
        if hasattr(state, "attempts"):
            state.attempts[action] = state.attempts.get(action, 0) + 1

        # Run the tool; many tools might not return anything and just mutate state
        result = tool.run(state)
        state.last_action = action
        return result