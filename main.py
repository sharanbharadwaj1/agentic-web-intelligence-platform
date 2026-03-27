from dotenv import load_dotenv
load_dotenv()

from orchestrator.manager import WorkflowManager
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wm = WorkflowManager()
res = wm.run_url_task({
    "url": "https://news.ycombinator.com",
    "task": "Extract top 5 headlines and summarize"
})
# res = wm.run_url_task({
#     "url": "https://timesofindia.indiatimes.com/india",
#     "task": "Extract top 5 headlines and summarize"
# })
# res = wm.run_url_task({
#     "url": "https://techcrunch.com",
#     "task": "Extract top 5 headlines and summarize"
# })

logger.info(f"Final result: {res}")
