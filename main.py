from dotenv import load_dotenv
load_dotenv()

from orchestrator.manager import WorkflowManager

wm = WorkflowManager()
res = wm.run_url_task({
    "url": "https://news.ycombinator.com",
    "task": "Extract top 5 headlines and summarize"
})
# res = wm.run_url_task({
#     "url": "https://timesofindia.indiatimes.com/india",
#     "task": "Extract top 5 headlines and summarize"
# })

print(f"Final result: {res}")
