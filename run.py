# import sqlite3
# con=sqlite3.connect('memory/sqlite.db')
# for row in con.execute("SELECT id, text, created_at FROM memory ORDER BY id DESC LIMIT 5"):
#     print(row)

from automation.manager import AutomationManager

am = AutomationManager()

am.run_watcher(
    url="https://news.ycombinator.com",
    task="Extract top headlines and summarize"
)

# B. Batch automation
am.run_batch(
    urls=[
        "https://news.ycombinator.com",
        "https://techcrunch.com"
    ],
    task="Extract top headlines and summarize"
)


# C. Time-based automation
am.run_scheduler(
    interval_seconds=3600,
    url="https://news.ycombinator.com",
    task="Extract top headlines and summarize"
)