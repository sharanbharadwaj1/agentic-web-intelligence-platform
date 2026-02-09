# tools/summarizer.py
class SummarizeTool:
    def run(self, state):
        if not state.headlines:
            raise RuntimeError("No headlines to summarize")

        text = "\n".join(state.headlines)
        state.summary = f"Summary of {len(state.headlines)} headlines."
        print(f"Summarizing {(state.headlines)} headlines")
        return state.summary
