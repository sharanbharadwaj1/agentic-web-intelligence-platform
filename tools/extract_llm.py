# tools/extract_llm.py
class ExtractLLMTool:
    def __init__(self, llm_client):
        self.llm = llm_client

    def run(self, state):
        prompt = f"Extract top headlines from this HTML:\n{state.html[:5000]}"
        headlines = self.llm.extract_headlines(prompt)

        state.headlines = headlines
        state.extract_strategy = "llm"
