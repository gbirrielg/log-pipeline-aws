import json
import re
from datetime import datetime

def validate_iso(date_string):
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except:
        return False
    return True


def handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # validate required fields
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
        
        # Valid log
        return {'statusCode': 200, 'body': json.dumps({'status': 'OK'})}
    
    except json.JSONDecodeError:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
