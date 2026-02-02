# tools/summarize.py
class SummarizeTool:
    def run(self, state):
        state.summary = " ".join(state.headlines[:2])