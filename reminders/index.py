import json
from datetime import datetime, timezone
from database import (
    create_reminder_db,
    get_reminders_by_user_id_db,
    get_reminder_by_id_db,
    update_reminder_db,
    delete_reminder_db
)


def handler(event, context):
    http_method = event.get("httpMethod", "UNKNOWN")
    path = event.get("path", "")

    if http_method == "POST" and path == "/reminders":
        return create_reminder(event)
    elif http_method == "GET" and path.startswith("/reminders/users/"):
        return get_reminders_by_user(event)
    elif http_method == "GET" and path.startswith("/reminders/"):
        return get_reminder(event)
    elif http_method == "PATCH" and path.startswith("/reminders/"):
        return update_reminder(event)
    elif http_method == "DELETE" and path.startswith("/reminders/"):
        return delete_reminder(event)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported HTTP method or path"})
        }


def create_reminder(event):
    try:
        body = json.loads(event.get("body", ""))
        user_id = body.get("user_id")
        title = body.get("title")
        reminder_time = body.get("reminder_time")
        description = body.get("description", None)

        if not user_id or not title or not reminder_time:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: 'user_id', 'title', or 'reminder_time'"})
            }

        try:
            reminder_time_parsed = datetime.fromisoformat(reminder_time)
        except ValueError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid 'reminder_time' format. Use ISO 8601 format (e.g., 2024-12-19T10:30:00Z)."})
            }

        if reminder_time_parsed <= datetime.now(timezone.utc):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "'reminder_time' must be in the future"})
            }

        reminder = create_reminder_db(user_id, title, reminder_time, description)
        return {
            "statusCode": 201,
            "body": json.dumps(reminder)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to create reminder: {str(e)}"})
        }


def get_reminders_by_user(event):
    try:
        path_parameters = event.get("pathParameters", {})
        user_id = path_parameters.get("user_id")

        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required path parameter: 'user_id'"})
            }

        reminders = get_reminders_by_user_id_db(int(user_id))
        return {
            "statusCode": 200,
            "body": json.dumps(reminders)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to retrieve reminders: {str(e)}"})
        }


def get_reminder(event):
    try:
        path_parameters = event.get("pathParameters", {})
        reminder_id = path_parameters.get("reminder_id")

        if not reminder_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required path parameter: 'reminder_id'"})
            }

        reminder = get_reminder_by_id_db(int(reminder_id))
        if not reminder:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"Reminder with ID '{reminder_id}' not found"})
            }

        return {
            "statusCode": 200,
            "body": json.dumps(reminder)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to retrieve reminder: {str(e)}"})
        }


def update_reminder(event):
    try:
        path_parameters = event.get("pathParameters", {})
        reminder_id = path_parameters.get("reminder_id")

        if not reminder_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required path parameter: 'reminder_id'"})
            }

        body = json.loads(event.get("body", "{}"))
        title = body.get("title")
        description = body.get("description")
        reminder_time = body.get("reminder_time")

        if reminder_time:
            try:
                reminder_time_parsed = datetime.fromisoformat(reminder_time)
                if reminder_time_parsed <= datetime.now(timezone.utc):
                    return {
                        "statusCode": 400,
                        "body": json.dumps({"error": "'reminder_time' must be in the future"})
                    }
            except ValueError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid 'reminder_time' format. Use ISO 8601 format."})
                }

        existing_reminder = get_reminder_by_id_db(int(reminder_id))
        if not existing_reminder:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"Reminder with ID '{reminder_id}' not found"})
            }

        update_reminder_db(int(reminder_id), title, description, reminder_time)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Reminder successfully updated"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to update reminder: {str(e)}"})
        }


def delete_reminder(event):
    try:
        path_parameters = event.get("pathParameters", {})
        reminder_id = path_parameters.get("reminder_id")

        if not reminder_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required path parameter: 'reminder_id'"})
            }

        existing_reminder = get_reminder_by_id_db(int(reminder_id))
        if not existing_reminder:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"Reminder with ID '{reminder_id}' not found"})
            }

        delete_reminder_db(int(reminder_id))
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Reminder successfully deleted"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to delete reminder: {str(e)}"})
        }
