import json
import os
import requests
from datetime import datetime, timezone
from database import get_pending_reminders_db, update_reminder_db

MAILERSEND_API_URL = "https://api.mailersend.com/v1/email"
MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")


def handler(event, context):
    try:
        now = datetime.now(timezone.utc).isoformat()
        pending_reminders = get_pending_reminders_db(now)

        if not pending_reminders:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No pending reminders to send."})
            }

        for reminder in pending_reminders:
            email_payload = {
                "from": {
                    "email": "noreply@trial-3z0vklo9jm1l7qrx.mlsender.net",
                    "name": "Reminder Service"
                },
                "to": [
                    {
                        "email": reminder["user_email"]
                    }
                ],
                "subject": f"Reminder: {reminder['title']}",
                "text": f"This is your reminder: {reminder['title']}.",
                "html": f"""
                    <p>This is your reminder:</p>
                    <p><strong>{reminder['title']}</strong></p>
                    <p>{reminder['description'] if reminder['description'] is not None else 'Нет деталей'}</p>
                """
            }

            response = requests.post(
                MAILERSEND_API_URL,
                headers={
                    "Authorization": f"Bearer {MAILERSEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=email_payload
            )

            if response.status_code != 202:
                continue

            update_reminder_db(reminder_id=reminder["id"], sent_at=now)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Emails sent successfully."})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to process reminders: {str(e)}"})
        }
