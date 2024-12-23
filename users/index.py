import json
import re
from database import (
    get_all_users_db,
    get_user_by_id_db,
    get_user_by_email_db,
    create_user_db,
    update_user_db
)


def handler(event, context):
    http_method = event.get("httpMethod", "UNKNOWN")

    print(json.dumps(event))

    if http_method == "POST":
        return create_new_user(event)
    elif http_method == "PATCH":
        return update_user(event)
    elif http_method == "GET":
        return get_all_users()
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported HTTP method"})
        }


def create_new_user(event):
    try:
        body = json.loads(event.get("body", ""))
        email = body.get("email")

        if not email or not is_valid_email(email):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": 'Invalid or missing "email" field in request body'})
            }

        existing_user = get_user_by_email_db(email)
        if existing_user:
            return {
                "statusCode": 409,
                "body": json.dumps({"error": f'User with email "{email}" already exists'})
            }

        new_user = create_user_db(email)
        return {
            "statusCode": 201,
            "body": json.dumps(new_user)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to create user: {str(e)}"})
        }


def update_user(event):
    try:
        path_parameters = event.get("pathParameters", {})
        user_id = path_parameters.get("user_id")
        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": 'Missing required path parameter: "user_id"'})
            }

        body = json.loads(event.get("body", "{}"))
        email = body.get("email")

        if not email or not is_valid_email(email):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": 'Invalid or missing "email" field in request body'})
            }

        existing_user = get_user_by_id_db(int(user_id))
        if not existing_user:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f'User with ID "{user_id}" not found'})
            }

        duplicate_email_user = get_user_by_email_db(email)
        if duplicate_email_user:
            return {
                "statusCode": 409,
                "body": json.dumps({"error": f'Email "{email}" is already in use'})
            }

        update_user_db(int(user_id), email)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "User successfully updated"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to update user: {str(e)}"})
        }


def get_all_users():
    try:
        users = get_all_users_db()
        return {
            "statusCode": 200,
            "body": json.dumps(users)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Failed to retrieve users: {str(e)}"})
        }


def is_valid_email(email):
    email_regex = r"^[^@]+@[^@]+\.[^@]+$"
    return re.match(email_regex, email) is not None
