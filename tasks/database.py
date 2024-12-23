import os
import datetime
import random
import ydb

driver_config = ydb.DriverConfig(
    endpoint=os.getenv('YDB_ENDPOINT'),
    database=os.getenv('YDB_DATABASE'),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

driver = ydb.Driver(driver_config)
driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)


def execute_query(query):
    return pool.retry_operation_sync(lambda session: session.transaction().execute(
        query,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))


def format_row(row):
    return {
        key: (value.decode('utf-8') if isinstance(value, bytes) else value)
        for key, value in row.items()
    }


def get_task_by_id_db(task_id):
    query = f"""
    SELECT task_id, user_id, title, description, attachment_url, is_completed, created_at, updated_at
      FROM tasks
     WHERE task_id = {task_id};
    """

    result = execute_query(query)

    if not result[0].rows:
        return None

    return format_row(result[0].rows[0])


def get_user_by_id(user_id):
    query = f"""
    SELECT user_id, email, created_at, updated_at
      FROM users
     WHERE user_id = {user_id};
    """

    result = execute_query(query)

    if not result[0].rows:
        return None

    return format_row(result[0].rows[0])


def get_user_tasks(user_id):
    query = f"""
    SELECT task_id, user_id, title, description, attachment_url, is_completed, created_at, updated_at
      FROM tasks
     WHERE user_id = {user_id};
    """

    result = execute_query(query)

    return [format_row(row) for row in result[0].rows]


def create_task(user_id, title, description, attachment_url=None):
    task_id = random.randint(0, 2**64 - 1)

    query = f"""
    INSERT INTO tasks (task_id, user_id, title, description, attachment_url, is_completed, created_at, updated_at)
    VALUES ({task_id}, {user_id}, '{title}', '{description}', 
            {f"'{attachment_url}'" if attachment_url else 'NULL'}, false, 
            '{datetime.datetime.utcnow().isoformat()}', NULL)
    RETURNING task_id;
    """

    result = execute_query(query)

    return {'task_id': result[0].rows[0]['task_id']}


def update_task_in_db(task_id, title=None, description=None, attachment_url=None, is_completed=None):
    updates = []

    if title:
        updates.append(f"title = '{title}'")

    if description:
        updates.append(f"description = '{description}'")

    if attachment_url:
        updates.append(f"attachment_url = '{attachment_url}'")

    if is_completed is not None:
        updates.append(f"is_completed = {str(is_completed).lower()}")

    query = f"""
    UPDATE tasks
       SET {', '.join(updates)}
         , updated_at = '{datetime.datetime.utcnow().isoformat()}'
     WHERE task_id = {task_id};
    """

    execute_query(query)


def delete_task_from_db(task_id):
    query = f"""
    DELETE FROM tasks
     WHERE task_id = {task_id};
    """

    execute_query(query)
