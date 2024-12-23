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


def execute_query_db(query):
    return pool.retry_operation_sync(lambda session: session.transaction().execute(
        query,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))


def format_row_db(row):
    return {
        key: (value.decode('utf-8') if isinstance(value, bytes) else value)
        for key, value in row.items()
    }


def get_all_users_db():
    query = """
    SELECT user_id, email, created_at, updated_at
      FROM users;
    """
    result = execute_query_db(query)

    return [format_row_db(row) for row in result[0].rows]


def get_user_by_id_db(user_id):
    query = f"""
    SELECT user_id, email, created_at, updated_at
      FROM users
     WHERE user_id = {user_id};
    """
    result = execute_query_db(query)

    if not result[0].rows:
        return None

    return format_row_db(result[0].rows[0])


def get_user_by_email_db(email):
    query = f"""
    SELECT user_id, email, created_at, updated_at
      FROM users
     WHERE email = '{email}';
    """
    result = execute_query_db(query)

    if not result[0].rows:
        return None

    return format_row_db(result[0].rows[0])


def create_user_db(email):
    user_id = random.randint(0, 2**64 - 1)
    query = f"""
    INSERT INTO users (user_id, email, created_at, updated_at)
    VALUES ({user_id}, '{email}', '{datetime.datetime.utcnow().isoformat()}', NULL)
    RETURNING user_id;
    """
    result = execute_query_db(query)

    return {'user_id': result[0].rows[0]['user_id']}


def update_user_db(user_id, email):
    query = f"""
    UPDATE users
       SET email = '{email}',
           updated_at = '{datetime.datetime.utcnow().isoformat()}'
     WHERE user_id = {user_id};
    """
    execute_query_db(query)
