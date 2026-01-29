import schedule
import time
from datetime import datetime
import requests

def send_reminder():
    # Check if draft is empty at 6 PM
    # Send WhatsApp message to owner
    message = "⏰ Reminder: Create tomorrow's order!"
    # Use Twilio or similar service
    print(f"Reminder sent at {datetime.now()}")

schedule.every().day.at("18:00").do(send_reminder)

while True:
    schedule.run_pending()
    time.sleep(60)