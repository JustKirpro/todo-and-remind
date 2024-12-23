import datetime
import random
import os
import boto3
import base64

BUCKET_NAME = 'todo-bucket'

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('ACCESS_SECRET_KEY')
)


def save_attachment_to_s3(base64_content, extension):
    object_key = f'tasks/{datetime.datetime.utcnow().isoformat()}-{random.randint(0, 9999)}.{extension}'
    file_content = base64.b64decode(base64_content)
    s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=file_content)

    return f'https://storage.yandexcloud.net/{BUCKET_NAME}/{object_key}'
