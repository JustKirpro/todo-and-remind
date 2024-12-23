import json
from database import (
    get_user_tasks,
    get_task_by_id_db,
    get_user_by_id,
    create_task,
    update_task_in_db,
    delete_task_from_db
)
from s3 import save_attachment_to_s3


def handler(event, context):
    http_method = event.get('httpMethod', 'UNKNOWN')
    path = event.get('path', '')

    try:
        if http_method == 'POST' and path == '/tasks':
            return create_new_task(event)
        elif http_method == 'GET' and path.startswith('/tasks/users/'):
            return get_tasks_by_user(event)
        elif http_method == 'GET' and path.startswith('/tasks/'):
            return get_task_by_id(event)
        elif http_method == 'PATCH' and path.startswith('/tasks/'):
            return update_task(event)
        elif http_method == 'DELETE' and path.startswith('/tasks/'):
            return delete_task(event)
        else:
            return generate_response(400, {'error': 'Unknown HTTP method or path'})
    except Exception as e:
        return generate_response(500, {'error': f'Unexpected server error: {str(e)}'})


def create_new_task(event):
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        title = body.get('title')
        description = body.get('description', '')
        attachment = body.get('attachment')

        if not user_id or not title:
            return generate_response(400, {'error': 'Missing required fields: "user_id" or "title"'})

        user = get_user_by_id(user_id)

        if not user:
            return generate_response(404, {'error': f'User with ID "{user_id}" not found'})

        attachment_url = handle_attachment(attachment)
        task = create_task(user_id, title, description, attachment_url)

        return generate_response(201, task)

    except Exception as e:
        return generate_response(500, {'error': f'Failed to create task: {str(e)}'})


def get_task_by_id(event):
    try:
        task_id = event.get('pathParameters', {}).get('task_id')

        if not task_id:
            return generate_response(400, {'error': 'Missing required path parameter: "task_id"'})

        task = get_task_by_id_db(task_id)
        if not task:
            return generate_response(404, {'error': f'Task with ID "{task_id}" not found'})

        return generate_response(200, task)

    except Exception as e:
        return generate_response(500, {'error': f'Failed to retrieve task: {str(e)}'})


def get_tasks_by_user(event):
    try:
        user_id = event.get('pathParameters', {}).get('user_id')

        if not user_id:
            return generate_response(400, {'error': 'Missing required path parameter: "user_id"'})

        user = get_user_by_id(user_id)
        if not user:
            return generate_response(404, {'error': f'User with ID "{user_id}" not found'})

        tasks = get_user_tasks(user_id)
        return generate_response(200, tasks)

    except Exception as e:
        return generate_response(500, {'error': f'Failed to retrieve tasks: {str(e)}'})


def update_task(event):
    try:
        task_id = event.get('pathParameters', {}).get('task_id')

        if not task_id:
            return generate_response(400, {'error': 'Missing required path parameter: "task_id"'})

        body = json.loads(event.get('body', '{}'))
        title = body.get('title')
        description = body.get('description')
        attachment = body.get('attachment')
        is_completed = body.get('is_completed')

        existing_task = get_task_by_id_db(task_id)
        if not existing_task:
            return generate_response(404, {'error': f'Task with ID "{task_id}" not found'})

        attachment_url = handle_attachment(attachment) or existing_task['attachment_url']
        update_task_in_db(
            task_id=task_id,
            title=title,
            description=description,
            attachment_url=attachment_url,
            is_completed=is_completed
        )

        return generate_response(200, {'message': 'Task successfully updated'})

    except Exception as e:
        return generate_response(500, {'error': f'Failed to update task: {str(e)}'})


def delete_task(event):
    try:
        task_id = event.get('pathParameters', {}).get('task_id')

        if not task_id:
            return generate_response(400, {'error': 'Missing required path parameter: "task_id"'})

        existing_task = get_task_by_id_db(task_id)
        if not existing_task:
            return generate_response(404, {'error': f'Task with ID "{task_id}" not found'})

        delete_task_from_db(task_id)
        return generate_response(200, {'message': 'Task successfully deleted'})

    except Exception as e:
        return generate_response(500, {'error': f'Failed to delete task: {str(e)}'})


def handle_attachment(attachment):
    if attachment:
        if 'base64' not in attachment or 'extension' not in attachment:
            raise ValueError('Both "base64" and "extension" are required for the attachment')
        return save_attachment_to_s3(attachment['base64'], attachment['extension'])
    return None


def generate_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }
