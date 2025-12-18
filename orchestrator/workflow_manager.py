# orchestrator/workflow_manager.py (improved run_url_task)
import os
import json
import time
import traceback
from typing import Dict, Any, List
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from pathlib import Path
from urllib.parse import urlparse

WORK_ROOT = Path("work")
WORK_ROOT.mkdir(exist_ok=True)

MAX_STEPS = 12  # safety cap

class WorkflowManager:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.critic = CriticAgent()

    def _safe_url(self, url: str) -> bool:
        try:
            p = urlparse(url)
            return p.scheme in ("http", "https") and bool(p.netloc)
        except Exception:
            return False

    def run_url_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: {"url":..., "task":..., "task_id":...}
        Returns: structured dict (status, steps, outputs, summary, errors)
        """
        url = payload.get("url")
        task = payload.get("task")
        task_id = payload.get("task_id", str(int(time.time())))

        if not url or not task:
            return {"task_id": task_id, "status": "failed", "error": "missing url or task"}

        if not self._safe_url(url):
            return {"task_id": task_id, "status": "failed", "error": "invalid url"}

        run_dir = WORK_ROOT / task_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Keep raw planner output for debugging
        planner_raw_path = run_dir / "planner_raw.txt"

        # 1) Get plan from PlannerAgent (URL-aware planner.plan(url, task))
        steps: List[str] = []
        try:
            steps = self.planner.plan(url, task)
            # persist raw steps for debugging
            with open(planner_raw_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"url": url, "task": task, "steps": steps}, ensure_ascii=False, indent=2))
        except Exception as e:
            # planner failure -> fallback deterministic plan (with URL inserted)
            steps = [s.format(url=url) for s in getattr(self.planner, "FALLBACK_PLAN", [
                "Fetch the webpage at {url}",
                "Parse the HTML and extract the target data",
                "Store the extracted data in memory",
                "Summarize the stored data",
                "Return the final report"
            ])]
            # log planner exception to planner_raw.txt
            with open(planner_raw_path, "a", encoding="utf-8") as f:
                f.write("\n\n[planner error]\n")
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())

        # Validate steps type and cap
        if not isinstance(steps, list):
            # attempt heuristic split of planner output string
            try:
                if isinstance(steps, str):
                    steps = [s.strip() for s in steps.splitlines() if s.strip()]
                else:
                    steps = list(steps)
            except Exception:
                steps = []

        # Ensure steps are strings and not empty
        norm_steps = []
        for s in steps:
            if not s:
                continue
            if not isinstance(s, str):
                s = str(s)
            norm_steps.append(s.strip())
        steps = norm_steps[:MAX_STEPS] if norm_steps else [f"Fetch the webpage at {url}", "Extract data", "Store in memory", "Summarize"]

        outputs = []
        errors = []

        # 2) Execute steps sequentially
        for idx, step in enumerate(steps, start=1):
            step_for_exec = step.replace("{url}", url)
            start_ts = time.time()
            try:
                result = self.executor.execute(step_for_exec)
                end_ts = time.time()
                # persist artifact
                out_path = run_dir / f"step_{idx}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "step": step_for_exec,
                        "result": result,
                        "start_ts": start_ts,
                        "end_ts": end_ts
                    }, f, ensure_ascii=False, indent=2)

                # Validate with CriticAgent (must accept lists/dicts/strings)
                try:
                    # valid = bool(self.critic.validate(step_for_exec, result))
                    # replace the critic.validate(...) call with this logic
                    if "store" in step_for_exec.lower() or "save" in step_for_exec.lower():
                        # consider storing successful if result is non-empty or a success message
                        if result is None:
                            valid = False
                        elif isinstance(result, (list, tuple)):
                            valid = len(result) > 0
                        elif isinstance(result, str):
                            valid = len(result.strip()) > 0 and "error" not in result.lower()
                        else:
                            valid = True
                    else:
                        valid = bool(self.critic.validate(step_for_exec, result))

                except Exception as ce:
                    valid = False
                    # record critic exception
                    errors.append({"step_index": idx, "step": step, "error": f"critic_failed: {ce}"})

                outputs.append({
                    "step_index": idx,
                    "step": step,
                    "exec_step": step_for_exec,
                    "result": result,
                    "valid": valid,
                    "start_ts": start_ts,
                    "end_ts": end_ts
                })

                if not valid:
                    errors.append({"step_index": idx, "step": step, "reason": "critic_rejected", "result": result})

            except Exception as e:
                end_ts = time.time()
                tb = traceback.format_exc()
                errors.append({"step_index": idx, "step": step, "error": str(e), "traceback": tb})
                outputs.append({
                    "step_index": idx,
                    "step": step,
                    "exec_step": step_for_exec,
                    "result": None,
                    "valid": False,
                    "start_ts": start_ts,
                    "end_ts": end_ts
                })
                # continue executing remaining steps by default; consider abort policy here
                continue

        # 3) Synthesize a final summary using executor.summarize_text or fallback
        summary = ""
        try:
            texts = []
            for o in outputs:
                r = o.get("result")
                if isinstance(r, list):
                    texts.extend([str(x) for x in r])
                elif isinstance(r, dict):
                    # flatten small dicts to text
                    try:
                        texts.append(json.dumps(r, ensure_ascii=False))
                    except Exception:
                        texts.append(str(r))
                elif r:
                    texts.append(str(r))
            text_blob = "\n".join(texts).strip()
            # prefer executor's summarizer (it uses Groq if available and local fallback)
            if hasattr(self.executor, "summarize_text"):
                summary = self.executor.summarize_text(text_blob)
            else:
                # simple fallback
                summary = (text_blob[:1000] + "...") if len(text_blob) > 1000 else text_blob or "No content to summarize."
        except Exception as e:
            summary = f"[error summarizing]: {e}"
            errors.append({"summary_error": str(e), "traceback": traceback.format_exc()})

        status = "completed" if not errors else "completed_with_errors"
        result = {
            "task_id": task_id,
            "status": status,
            "url": url,
            "task": task,
            "steps": steps,
            "outputs": outputs,
            "summary": summary,
            "errors": errors
        }

        # persist final report
        try:
            with open(run_dir / "result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return result
