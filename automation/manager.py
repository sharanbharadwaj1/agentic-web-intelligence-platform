from automation.watcher import ChangeWatcher
from automation.scheduler import IntervalScheduler
from automation.pipeline import BatchPipeline
from automation.notifier import Notifier

class AutomationManager:
    """
    Single entry-point for all automations.
    """
    def __init__(self):
        self.notifier = Notifier()

    def run_watcher(self, url: str, task: str):
        watcher = ChangeWatcher(url, task)
        result = watcher.check()
        if result:
            self.notifier.notify(result)

    def run_batch(self, urls: list[str], task: str):
        pipeline = BatchPipeline(urls, task)
        results = pipeline.run()
        for r in results:
            self.notifier.notify(r)

    def run_scheduler(self, interval_seconds: int, url: str, task: str):
        scheduler = IntervalScheduler(interval_seconds, url, task)
        scheduler.start()
