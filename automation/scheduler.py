import time
from orchestrator.workflow_manager import WorkflowManager

class IntervalScheduler:
    """
    Runs workflow every N seconds.
    """
    def __init__(self, interval_seconds: int, url: str, task: str):
        self.interval = interval_seconds
        self.url = url
        self.task = task
        self.wm = WorkflowManager()

    def start(self):
        print("[Scheduler] Started")
        while True:
            print("[Scheduler] Executing workflow")
            self.wm.run_url_task({
                "url": self.url,
                "task": self.task
            })
            time.sleep(self.interval)
