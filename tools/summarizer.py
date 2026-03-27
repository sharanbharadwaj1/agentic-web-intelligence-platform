# tools/summarizer.py

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class SummarizeTool:
    def summarize(self, state):
        print("Reaching summarization step...")
        if not state.headlines:
            raise RuntimeError("No headlines to summarize")

        text = "\n".join(state.headlines)
        print(f"{state.headlines=}")
        logger.info(f"[DEBUG]State of headlines :{state.headlines}")
        state.summary = f"Summary of {len(state.headlines)} headlines."
        logger.info(f"Summarizing {(state.headlines)} headlines")
        return state.summary
    
    def run(self, state):
        state.summary = self.summarize(state)

        
        return {
            "summary": state.summary,
            "summary_strategy": "rule"
        }
