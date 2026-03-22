import json
import re
import os
import boto3
from datetime import datetime

sqs_client = boto3.client('sqs')
QUEUE_URL = os.environ.get('QUEUE_URL', '')

def validate_iso(date_string):
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except:
        return False
    return True


def handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Validate required fields and queue's existence
        if 'service_id' not in body or not isinstance(body['service_id'], str):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing or invalid service_id'})}

        if 'timestamp' not in body or not isinstance(body['timestamp'], str):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing or invalid timestamp'})}
        if not validate_iso(body['timestamp']):
            return {'statusCode': 400, 'body': json.dumps({'error': 'timestamp must be ISO 8601 UTC format'})}

        if 'status' not in body or not isinstance(body['status'], str):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing or invalid status'})}

        if 'latency_ms' not in body or not isinstance(body['latency_ms'], int):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing or invalid latency_ms'})}

        if not QUEUE_URL:
            return {'statusCode': 500, 'body': json.dumps({'error': 'QUEUE_URL is not configured'})}

        # Only include necessary fields in the message sent to SQS
        log_msg = {
            'service_id': body['service_id'],
            'timestamp': body['timestamp'],
            'status': body['status'],
            'latency_ms': body['latency_ms']
        }
        send_result = sqs_client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(log_msg)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'OK', 'message_id': send_result.get('MessageId')})
        }
    
    except json.JSONDecodeError:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
