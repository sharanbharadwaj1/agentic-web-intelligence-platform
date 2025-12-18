class Notifier:
    def notify(self, result: dict):
        status = result.get("status")
        if status != "completed":
            print("[NOTIFY] Workflow issue:", result.get("task_id"))
        else:
            print("[NOTIFY] Workflow success:", result.get("task_id"))
