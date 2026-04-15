import json
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import boto3

s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

RAW_LOGS_BUCKET = os.environ.get('RAW_LOGS_BUCKET', '')
METRICS_TABLE = os.environ.get('METRICS_TABLE', '')

TTL_SECONDS = {
    '1m': int(timedelta(hours=6).total_seconds()),
    '1h': int(timedelta(days=7).total_seconds()),
    '1d': int(timedelta(days=30).total_seconds()),
}

VALID_STATUSES = {'INFO', 'SUCCESS', 'ERROR'}


def truncate_windows(ts: datetime) -> dict[str, str]:
    minute = ts.replace(second=0, microsecond=0)
    hour = ts.replace(minute=0, second=0, microsecond=0)
    return {
        '1m': minute.isoformat(),
        '1h': hour.isoformat(),
        '1d': ts.date().isoformat(),
    }


def parse_log(body: str) -> dict | None:
    try:
        log = json.loads(body)
        ts = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
        if log.get('status') not in VALID_STATUSES:
            return None
        return {'service_id': log['service_id'], 'ts': ts, 'status': log['status'], 'raw': body}
    except Exception:
        return None


def build_aggregates(logs: list[dict]) -> dict:
    agg = defaultdict(lambda: {'INFO': 0, 'SUCCESS': 0, 'ERROR': 0})
    for log in logs:
        for window_type, window_start in truncate_windows(log['ts']).items():
            agg[(log['service_id'], window_type, window_start)][log['status']] += 1
    return agg


def write_to_dynamodb(agg: dict, now_epoch: int) -> None:
    for (service_id, window_type, window_start), counts in agg.items():
        expires_at = now_epoch + TTL_SECONDS[window_type]
        sk = f"{window_type}#{window_start}"

        dynamodb_client.update_item(
            TableName=METRICS_TABLE,
            Key={
                'service_id': {'S': service_id},
                'sk':         {'S': sk},
            },
            UpdateExpression=(
                'SET #counts.#INFO    = if_not_exists(#counts.#INFO,    :zero) + :info_n, '
                    '#counts.#SUCCESS = if_not_exists(#counts.#SUCCESS, :zero) + :success_n, '
                    '#counts.#ERROR   = if_not_exists(#counts.#ERROR,   :zero) + :error_n, '
                    '#total           = if_not_exists(#total,           :zero) + :total_n, '
                    '#window_type     = :window_type, '
                    '#window_start    = :window_start, '
                    'expires_at       = :expires_at'
            ),
            ExpressionAttributeNames={
                '#counts':       'counts',
                '#INFO':         'INFO',
                '#SUCCESS':      'SUCCESS',
                '#ERROR':        'ERROR',
                '#total':        'total',
                '#window_type':  'window_type',
                '#window_start': 'window_start',
            },
            ExpressionAttributeValues={
                ':zero':         {'N': '0'},
                ':info_n':       {'N': str(counts['INFO'])},
                ':success_n':    {'N': str(counts['SUCCESS'])},
                ':error_n':      {'N': str(counts['ERROR'])},
                ':total_n':      {'N': str(sum(counts.values()))},
                ':window_type':  {'S': window_type},
                ':window_start': {'S': window_start},
                ':expires_at':   {'N': str(expires_at)},
            },
        )


def handler(event, context):
    if not RAW_LOGS_BUCKET:
        raise RuntimeError('RAW_LOGS_BUCKET is not configured')
    if not METRICS_TABLE:
        raise RuntimeError('METRICS_TABLE is not configured')

    records = event.get('Records', [])
    raw_bodies = []
    parsed_logs = []

    for record in records:
        body = record.get('body', '')
        raw_bodies.append(body)
        log = parse_log(body)
        if log:
            parsed_logs.append(log)
        else:
            print(f"Skipping malformed record: {body[:200]}")

    # Write raw NDJSON to S3
    now = datetime.now(timezone.utc)
    s3_key = (
        f"raw/year={now:%Y}/month={now:%m}/day={now:%d}/hour={now:%H}/"
        f"logs-{now:%Y%m%dT%H%M%SZ}-{context.aws_request_id}.ndjson"
    )
    s3_client.put_object(
        Bucket=RAW_LOGS_BUCKET,
        Key=s3_key,
        Body="\n".join(raw_bodies).encode('utf-8'),
        ContentType='application/x-ndjson',
    )

    # Aggregate and write to DynamoDB
    if parsed_logs:
        now_epoch = int(now.timestamp())
        agg = build_aggregates(parsed_logs)
        write_to_dynamodb(agg, now_epoch)
        print(f"Updated {len(agg)} DynamoDB buckets from {len(parsed_logs)} valid logs")

    print(
        f"Processed {len(records)} SQS records "
        f"({len(parsed_logs)} valid) → s3://{RAW_LOGS_BUCKET}/{s3_key}"
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'OK',
            'processed': len(records),
            'valid': len(parsed_logs),
            's3_key': s3_key,
        }),
    }
