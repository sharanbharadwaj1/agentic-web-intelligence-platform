# from orchestrator.workflow_manager import WorkflowManager

# if __name__ == "__main__":
#     wm = WorkflowManager()
    
#     task = """
#     Scrape the top headlines from Hacker News, 
#     store them in memory, 
#     then summarize them into one final report.
#     """
    
#     outputs = wm.run_custom(task)

#     print("\n=== FINAL OUTPUT ===")
#     for item in outputs:
#         print(item)

#with automation
# def main():
#     print("AI Agent Platform initialized")

# if __name__ == "__main__":
#     main()

# main.py
from orchestrator.workflow_manager import WorkflowManager
import json
import time

def main():
    wm = WorkflowManager()

    # --- CHANGE THESE INPUTS AS NEEDED ---
    url = "https://timesofindia.indiatimes.com/india"
    # url = "https://www.hindustantimes.com/"
    task = "Extract top 10 headlines and give a two-sentence summary."

    print("\n=== RUNNING SINGLE WORKFLOW ===")
    print("URL:", url)
    print("TASK:", task)
    print("=" * 40)

    result = wm.run_url_task({
        "url": url,
        "task": task,
        "task_id": f"manual-{int(time.time())}"
    })

    print("\n=== FINAL SUMMARY ===")
    print(result.get("summary"))

    print("\n=== STATUS ===")
    print(result.get("status"))

    print("\n=== FULL RESULT (JSON) ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()



