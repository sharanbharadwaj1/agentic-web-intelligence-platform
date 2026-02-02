# agents/executor.py
class ExecutorAgent:
    def __init__(self, registry):
        self.registry = registry

    def execute(self, action, state):
        tool = self.registry.get(action)
        tool.run(state)
        state.last_action = action
