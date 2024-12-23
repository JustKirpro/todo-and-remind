import os
import datetime
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


def get_pending_reminders_db(now):
    query = f"""
    SELECT r.id AS id, r.user_id AS user_id, u.email AS user_email, r.title AS title, r.description AS description, r.reminder_time AS reminder_time
      FROM reminders r
      JOIN users u ON r.user_id = u.user_id
     WHERE r.sent_at IS NULL AND r.reminder_time <= '{now}';
    """

    result = execute_query(query)
    return [format_row(row) for row in result[0].rows]


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
