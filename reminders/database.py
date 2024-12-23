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


def create_reminder_db(user_id, title, reminder_time, description=None):
    reminder_id = random.randint(0, 2**64 - 1)
    created_at = datetime.datetime.utcnow().isoformat()

    query = f"""
    INSERT INTO reminders (id, user_id, title, description, reminder_time, created_at, updated_at, sent_at)
    VALUES ({reminder_id}, {user_id}, '{title}', {f"'{description}'" if description else 'NULL'}, 
            '{reminder_time}', '{created_at}', NULL, NULL)
    RETURNING id, user_id, title, description, reminder_time, created_at, updated_at, sent_at;
    """

    result = execute_query(query)
    return format_row(result[0].rows[0])


def get_reminders_by_user_id_db(user_id):
    query = f"""
    SELECT id, user_id, title, description, reminder_time, created_at, updated_at
    FROM reminders
    WHERE user_id = {user_id};
    """

    result = execute_query(query)
    return [format_row(row) for row in result[0].rows]


def get_reminder_by_id_db(reminder_id):
    query = f"""
    SELECT id, user_id, title, description, reminder_time, created_at, updated_at
    FROM reminders
    WHERE id = {reminder_id};
    """

    result = execute_query(query)
    if not result[0].rows:
        return None

    return format_row(result[0].rows[0])


def update_reminder_db(reminder_id, title=None, description=None, reminder_time=None, sent_at=None):
    updates = []

    if title:
        updates.append(f"title = '{title}'")
    if description:
        updates.append(f"description = '{description}'")
    if reminder_time:
        updates.append(f"reminder_time = '{reminder_time}'")
    if sent_at:
        updates.append(f"sent_at = '{sent_at}'")

    if not updates:
        return

    query = f"""
    UPDATE reminders
    SET {', '.join(updates)},
        updated_at = '{datetime.datetime.utcnow().isoformat()}'
    WHERE id = {reminder_id};
    """

    execute_query(query)


def delete_reminder_db(reminder_id):
    query = f"""
    DELETE FROM reminders
    WHERE id = {reminder_id};
    """

    execute_query(query)
