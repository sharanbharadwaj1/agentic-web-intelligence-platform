from orchestrator.workflow_manager import WorkflowManager

class BatchPipeline:
    """
    Runs the same task across multiple URLs.
    """
    def __init__(self, urls: list[str], task: str):
        self.urls = urls
        self.task = task
        self.wm = WorkflowManager()

    def run(self):
        results = []
        for url in self.urls:
            print(f"[Pipeline] Running for {url}")
            result = self.wm.run_url_task({
                "url": url,
                "task": self.task
            })
            results.append(result)
        return results
