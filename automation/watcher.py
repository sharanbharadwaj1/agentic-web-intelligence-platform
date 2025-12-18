import hashlib
import time
from tools.web_scraper import WebScraper
from orchestrator.workflow_manager import WorkflowManager

class ChangeWatcher:
    """
    Runs workflow ONLY if website content changes.
    """
    def __init__(self, url: str, task: str):
        self.url = url
        self.task = task
        self.scraper = WebScraper()
        self.wm = WorkflowManager()
        self.last_hash = None

    def check(self):
        html = self.scraper.fetch(self.url)
        current_hash = hashlib.md5(html.encode("utf-8")).hexdigest()

        if self.last_hash != current_hash:
            print(f"[Watcher] Change detected for {self.url}")
            self.last_hash = current_hash
            return self.wm.run_url_task({
                "url": self.url,
                "task": self.task
            })

        print(f"[Watcher] No change for {self.url}")
        return None
