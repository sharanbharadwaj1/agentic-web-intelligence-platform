# agents/critic.py
from llm.groq_client import GroqClient

class CriticAgent:
    def __init__(self):
        self.llm = GroqClient()

    # def validate(self, step: str, result: str) -> bool:
    #     """
    #     Use Groq to validate output; but be defensive. If Groq is unavailable, fall back to a simple local check.
    #     """
    #     if not step or not result:
    #         return False

    #     try:
    #         prompt = f"""
    #         Evaluate whether the RESULT below satisfies the STEP.
    #         Answer only YES or NO.

    #         STEP:
    #         {step}

    #         RESULT:
    #         {result}
    #         """
    #         resp = self.llm.ask(prompt)
    #         if not resp:
    #             return False
    #         low = resp.lower()
    #         if "yes" in low and "no" not in low:
    #             return True
    #         if "no" in low and "yes" not in low:
    #             return False
    #         # ambiguous -> fallback to basic length heuristic
    #     except Exception:
    #         pass

    #     # fallback heuristic
    #     return len(result) > 10
    def validate(self, step: str, result: any) -> bool:
        # normalize
        if isinstance(result, (list, tuple)):
            result_text = "\n".join(map(str, result))
        else:
            result_text = str(result)

        # quick local rules before LLM:
        low_step = step.lower()
        if "extract" in low_step or "headline" in low_step or "fetch" in low_step:
            return len(result_text.strip()) > 5  # simple and robust

        if "store" in low_step:
            return len(result_text.strip()) > 0 and "error" not in result_text.lower()

        if "summarize" in low_step or "summary" in low_step:
            # accept if it's a short paragraph (heuristic)
            return len(result_text.strip()) > 20 and "." in result_text.strip()

        # otherwise use LLM if available, else fallback to length heuristic
        try:
            if self.llm:
                prompt = f"Does the RESULT below satisfy the STEP? Answer YES or NO.\n\nSTEP:\n{step}\n\nRESULT:\n{result_text}\n"
                resp = self.llm.ask(prompt)
                if resp:
                    low = resp.lower()
                    if "yes" in low and "no" not in low:
                        return True
                    if "no" in low and "yes" not in low:
                        return False
        except Exception:
            pass

        return len(result_text.strip()) > 10

