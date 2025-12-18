# api/server.py
import uuid
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from orchestrator.workflow_manager import WorkflowManager

app = FastAPI(title="Agent Orchestrator API")
wm = WorkflowManager()  # keep single orchestrator in process (simple)

class RunRequest(BaseModel):
    url: HttpUrl
    task: str
    sync: bool = True   # if false, returns task_id and runs in background

class RunResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None

@app.post("/run", response_model=RunResponse)
def run(request: RunRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    # basic validation
    if len(request.task.strip()) < 3:
        raise HTTPException(status_code=400, detail="task is too short")

    payload = {"url": str(request.url), "task": request.task, "task_id": task_id}

    if not request.sync:
        background_tasks.add_task(wm.run_url_task, payload)
        return {"task_id": task_id, "status": "accepted", "result": None}

    try:
        result = wm.run_url_task(payload)
        return {"task_id": task_id, "status": result.get("status", "ok"), "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
