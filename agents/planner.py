# # agents/planner.py

from asyncio.log import logger
import json
from typing import Optional, Dict, Any
from agents.agent_helper.planner_validation import validate_planner_output
from llm.groq_client import GroqClient
from agents.agent_helper.planner_prompt import planner_agent_prompt
from agents.agent_helper.planner_schema import planner_agent_schema
from agents.agent_helper.utils import looks_blocked
from tools.utils.fetch_helper import looks_js_rendered
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlannerAgent:
    """
    Stateful, LLM-based planner.

    Given the current state of the scraping workflow (html/headlines/summary),
    decides the NEXT action to take:
        - fetch_static
        - fetch_selenium
        - extract_rule
        - summarize
        - finish
    """

    def __init__(self, model_name: Optional[str] = None):
        self.llm = GroqClient(model_name) if model_name is None else GroqClient(model_name=model_name)

    def _looks_like_error(self, text: Optional[str]) -> bool:
        if not text:
            return True
        low = text.lower()
        markers = [
            "error", "exception", "quota", "not-available", "resourceexhausted",
            "model_not_found", "traceback", "[groq error]"
        ]
        return any(m in low for m in markers)

    def _fallback_decide(self, state) -> Dict[str, str]:
        """
        Deterministic backup: same logic as your original state-based planner.
        """

        logger.info("PlannerAgent FALLBACK_DECIDE invoked.")
        if state.scrape_strategy == "static" and looks_js_rendered(state.html):
            return {"action": "fetch_selenium", "reason": "Static page appears JS-rendered"}
        
        if (
            state.scrape_strategy == "static"
            and state.html
            and looks_js_rendered(state.html)
        ):
            return {
                "action": "fetch_selenium",
                "reason": "Static extraction rejected; page is JS-rendered"
            }   

        if state.html is not None:
        # never fetch again unless explicitly invalidated
            pass


        if state.html is None:
            return {"action": "fetch_static", "reason": "Try static scrape first"}
        
        

        if state.html is None and looks_blocked(state.html):
            return {"action": "fetch_selenium", "reason": "Static page appears blocked"}
        
      
        

        if state.headlines is None:
            return {"action": "extract_rule", "reason": "Try rule-based extraction"}
        
        if (state.headlines is None
        and state.attempts["extract_rule"] >= 2 ): # after 2 tries of rule-based extraction)
            return {
            "action": "extract_llm",
            "reason": "Rule-based extraction failed multiple times"
                }

        if state.summary is None:
            return {"action": "summarize", "reason": "Generate summary"}

        return {"action": "finish", "reason": "Goal reached"}

    def decide(self, state) -> Dict[str, Any]:
        """
        Use the LLM to decide the next action based on current state.

        Returns:
            {
                "action": "<one of: fetch_static, fetch_selenium, extract_rule, summarize, finish>",
                "reason": "<short natural language justification>",
            }
        """


        logger.info(
                f"[DEBUG] last_action={state.last_action} | "
                f"last_critic={state.last_critic_feedback} | "
                f"attempts={state.attempts}"
            )

        if not state.url or not state.goal:
            logger.info("PlannerAgent: Missing url or task in state, invoking fallback.")
            return self._fallback_decide(state)
        
        logger.info(f"[Planner.decide] entered | url={state.url} | goal={state.goal}")



        # Prepare a serialized view of state for the LLM (keep it compact)
        logger.info(f"Current state before decision: html={'present' if state.html else 'missing'}, headlines={'present' if state.headlines else 'missing'}, summary={'present' if state.summary else 'missing'}")
        html_status = (
            "missing"
            if state.html is None else
            ("HTML scraping BLOCKED'" if looks_blocked(state.html) else "present")
        )
        headlines_status = "missing" if state.headlines is None else "present"
        summary_status = "missing" if state.summary is None else "present"

        # You can expand this if you keep more info in state (errors, attempts, etc.)
        state_description = {
            "url": state.url,
            "task": state.goal,
            "html_status": html_status,
            "headlines_status": headlines_status,
            "summary_status": summary_status,
        }

        try:
            if (
                state.html is not None
                and state.last_action == "extract_rule"
                and state.last_critic_feedback == "STATIC_EXTRACTION_LOW_QUALITY"
                and state.attempts.get("extract_rule", 0) >= 1
            ):
                return {
                    "action": "fetch_selenium",
                    "reason": "Rule-based extraction repeatedly low quality; switching to JS-rendered fetch",
                }

            if state.attempts.get("extract_rule", 0) >= 3:
                return {
                    "action": "fetch_selenium",
                    "reason": "Exceeded rule-based extraction retries",
                }
            
            if (
                getattr(state, "last_action", None) == "extract_rule"
                and getattr(state, "last_critic_feedback", None) == "STATIC_EXTRACTION_LOW_QUALITY"
                and state.attempts.get("extract_rule", 0) >= 1
            ):  
                logger.info("[last]PlannerAgent: Detected repeated low-quality extraction, escalating to Selenium fetch.")
                return {
                    "action": "fetch_selenium",
                    "reason": "Rule-based extraction low quality; switching to JS-rendered fetch",
                }
        except Exception as e:
            logger.info(f"Error in pre-LLM escalation logic: {e}")

        # Structured prompt: ask for the next action + reason
        try:
            # 🚨 HARD GUARD: never refetch static HTML once present
            if state.html is not None:
                # If HTML exists, move forward deterministically
                if state.headlines is None:
                    return {
                        "action": "extract_rule",
                        "reason": "HTML already present, proceed to extract headlines",
                    }
                if state.summary is None:
                    return {
                        "action": "summarize",
                        "reason": "Headlines present, generate summary",
                    }
                return {
                    "action": "finish",
                    "reason": "Goal reached",
                }
            
            # 🚨 Escalation: rule-based extraction is failing
            # 🚨 Escalation: rule-based extraction is failing
            




            state_desc_json=json.dumps(state_description, indent=2)
            prompt = planner_agent_prompt.format(state_desc=state_desc_json)
            # logger.info(f"Prepared prompt for PlannerAgent:\n{prompt}")
        except Exception as e:
            logger.info(f"Error preparing prompt: {e}")
            raise RuntimeError(f"Failed to prepare prompt for PlannerAgent :{e}") from e


        # schema = planner_agent_schema

        # Try structured LLM call
        try:
            logger.info("PlannerAgent sending prompt to LLM...")
            response_text = self.llm.structured(prompt, schema=None)
            # logger.info(f"Planner LLM response: {response_text}")
        except Exception as e:
            response_text = f"[Groq Error] {e}"

        if state.scrape_strategy == "static" and looks_js_rendered(state.html):
            logger.info("Detected JS-rendered page in fallback logic.")
            return {"action": "fetch_selenium", "reason": "Static page appears JS-rendered"}

        # If LLM failed badly, fallback to deterministic logic
        if self._looks_like_error(response_text):
            return self._fallback_decide(state)
        
        
        try:
            parsed = json.loads(response_text)

        except Exception:
            logger.warning("Planner returned invalid JSON, falling back")
            return self._fallback_decide(state)
        
        if not validate_planner_output(parsed):
            logger.warning("Planner returned invalid output, falling back")
            return self._fallback_decide(state)

        action = parsed.get("action")
        reason = parsed.get("reason")

        if action not in {
            "fetch_static",
            "fetch_selenium",
                "extract_rule",
                "extract_llm",
            "summarize",
            "finish",
        }:
            logger.warning(f"Planner returned invalid action: {action}")
            return self._fallback_decide(state)

        if not isinstance(reason, str) or not reason.strip():
            reason = "LLM decision"

        return {
                "action": action,
                "reason": reason,
            }



