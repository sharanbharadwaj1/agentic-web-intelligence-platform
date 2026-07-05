# orchestrator.py
import json
import re
import time
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
import logging


from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.agent_helper.normalizer_error import normalize_error
# from orchestrator.utils.cleaner import cleanup_dirs_keep_recent
from tools.registry import ToolRegistry
from tools.extract_llm import ExtractLLMTool
from tools.extract_rule import ExtractRuleTool
from tools.fetch_selenium import FetchSeleniumTool
from tools.fetch_static import FetchStaticTool
from tools.summarizer import SummarizeTool
from state import AgentState
from llm.groq_client import GroqClient  # or whatever LLM client you use

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORK_ROOT = Path("work")
WORK_ROOT.mkdir(exist_ok=True)

MAX_STEPS = 6


def _safe_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


class WorkflowManager:
    def __init__(self):
        # tools registry
        self.registry = ToolRegistry()
        llm_client = GroqClient()

        self.registry.register("fetch_static", FetchStaticTool())
        self.registry.register("fetch_selenium", FetchSeleniumTool())
        self.registry.register("extract_rule", ExtractRuleTool())
        self.registry.register("extract_llm", ExtractLLMTool(llm_client))
        self.registry.register("summarize", SummarizeTool())

        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(self.registry)
        self.critic = CriticAgent()  # separate component

    def run_url_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: {"url":..., "task":..., "task_id":...}
        Returns: {"task_id", "status", "url", "task", "steps_trace", "summary", "errors"}
        """
        url = payload.get("url")
        task = payload.get("task")
        task_id = payload.get("task_id", str(int(time.time())))

        if not url or not task:
            return {"task_id": task_id, "status": "failed", "error": "missing url or task"}

        if not _safe_url(url):
            return {"task_id": task_id, "status": "failed", "error": "invalid url"}

        run_dir = WORK_ROOT / task_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # initialize state
        state = AgentState(goal=task, url=url)
        # optional meta fields
        if not hasattr(state, "task_id"):
            setattr(state, "task_id", task_id)
        if not hasattr(state, "steps_trace"):
            setattr(state, "steps_trace", [])
        if not hasattr(state, "errors"):
            setattr(state, "errors", [])

        step_counter = 0

        while True:
            step_counter += 1
            if step_counter > MAX_STEPS:
                state.errors.append(str(f"max_steps_exceeded:{MAX_STEPS}"))
                break

            # 1) planner decides next action based on current state
            try:
                decision = self.planner.decide(state)
            except Exception as e:
                state.errors.append(str(f"planner_failed:{e}"))
                break

            action = decision.get("action") 
            reason = decision.get("reason", "")
            logger.info(f"Planner decision at step {step_counter}: action={action}, reason={reason}")

            # finish condition
            if action == "finish":
                state.steps_trace.append({
                    "step_index": step_counter,
                    "planner_action": action,
                    "planner_reason": reason,
                })
                break

            # record decision
            trace_entry = {
                "step_index": step_counter,
                "planner_action": action,
                "planner_reason": reason,
            }

            # 2) execute action (uses tools via registry)
            start_ts = time.time()
            exec_error = None
            try:
                self.executor.execute(action, state)
            except Exception as e:
                # exec_error = e
                # state.errors.append(str(f"executor_failed[{action}]:{e}"))
                logger.error(f"Execution failed for action {action}: {e}")
                exec_error = e
                if hasattr(state, "add_error"):
                    state.add_error(
                        action=action,
                        message=str(e),
                        recoverable=True
                    )
                else:
                    state.errors.append({
                        "action": action,
                        "message": str(e),
                        "recoverable": True
                    })


                # simple recovery/fallback logic, like your loop example
                try:
                    if action == "extract_rule":
                        fallback_extraction = "extract_llm"
                        logging.info(f"Fallback :{fallback_extraction} ,Rule bases extraction Failed. Switched to LLM extraction")
                        self.executor.execute("extract_llm",state)
                    elif action == "fetch_static":
                        self.executor.execute("fetch_selenium", state)
                        action = "fetch_selenium"
                except Exception as e2:
                    state.errors.append(str(f"fallback_failed[{action}]:{e2}"))
            end_ts = time.time()

            # 3) critic validates current state – separate component
            critic_ok = True
            critic_feedback = ""
            try:
                critic_ok, critic_feedback = self.critic.validate(state)
            except Exception as e:
                critic_ok = False
                critic_feedback = f"critic_failed:{e}"
                state.errors.append(str(critic_feedback))

            # record last action
            state.last_action = action

            # increment attempts
            state.attempts[action] = state.attempts.get(action, 0) + 1

            # record critic feedback
            state.last_critic_feedback = critic_feedback

            # 🚨 Invalidate bad extraction
            if critic_feedback == "STATIC_EXTRACTION_LOW_QUALITY":
                state.headlines = None


            trace_entry.update({
                "executed_action": action,
                "exec_error": str(exec_error) if exec_error else None,
                "critic_ok": critic_ok,
                "critic_feedback": critic_feedback,
                "start_ts": start_ts,
                "end_ts": end_ts,
            })
            state.steps_trace.append(str(trace_entry))

            

        
        if action == "fetch_selenium":
            state.attempts["extract_rule"] = 0


        # Ensure we have a summary (either from summarize tool or derive)
        if not getattr(state, "summary", None):
            try:
                summarize_tool = SummarizeTool()
                if getattr(state, "headlines", None):
                    state.summary = summarize_tool.run(state)
                elif getattr(state, "html", None):
                    html_text = re.sub(r"<[^>]+>", " ", str(state.html))
                    html_text = re.sub(r"\s+", " ", html_text).strip()
                    state.summary = (
                        "HTML fallback summary: "
                        + (html_text[:300] if html_text else "No readable text found in HTML.")
                    )
                else:
                    print("No content available for summarization.")
                    state.summary = "No content to summarize."
            except Exception as e:
                state.summary = f"[error summarizing]: {e}"
                state.errors.append(str(e))


        errors_list = list(getattr(state, "errors", []))
        # 🔧 normalize legacy string errors → dicts
        errors_list = [normalize_error(e) for e in errors_list]
        state.errors = errors_list

        has_terminal_error = any(
        not err["recoverable"]
        for err in errors_list
    )

        status = (
            "failed"
            if has_terminal_error and not state.summary
            else "completed_with_errors"
            if errors_list
            else "completed"
        )






        result = {
            "task_id": task_id,
            "status": status,
            "url": url,
            "task": task,
            "steps_trace": state.steps_trace,
            "summary": state.summary,
            "errors": errors_list,
        }

        # persist final result
        try:
            with open(run_dir / "result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return result
