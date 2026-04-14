import json
import os
from datetime import datetime, timezone
import boto3

s3_client = boto3.client('s3')
RAW_LOGS_BUCKET = os.environ.get('RAW_LOGS_BUCKET', '')


def handler(event, context):
    records = event.get('Records', [])
    processed_count = len(records)

    if not RAW_LOGS_BUCKET:
        raise RuntimeError('RAW_LOGS_BUCKET is not configured')

    raw_logs = []
    for record in records:
        raw_logs.append(record.get('body', '{}'))

    now = datetime.now(timezone.utc)
    key = (
        f"raw/year={now:%Y}/month={now:%m}/day={now:%d}/hour={now:%H}/"
        f"logs-{now:%Y%m%dT%H%M%SZ}-{context.aws_request_id}.ndjson"
    )

    payload = "\n".join(raw_logs)
    s3_client.put_object(
        Bucket=RAW_LOGS_BUCKET,
        Key=key,
        Body=payload.encode('utf-8'),
        ContentType='application/x-ndjson'
    )

    print(f"Processed {processed_count} messages from SQS and wrote raw logs to s3://{RAW_LOGS_BUCKET}/{key}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'OK',
            'processed_messages': processed_count,
            's3_key': key
        })
    }
