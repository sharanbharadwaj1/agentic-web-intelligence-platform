
from apscheduler.schedulers.background import BackgroundScheduler

def scheduled_scrape():
    print("Running daily scrape job...")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_scrape, "interval", hours=24)
    scheduler.start()
