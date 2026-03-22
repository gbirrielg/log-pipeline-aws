import json


def handler(event, context):
    records = event.get('Records', [])
    processed_count = len(records)

    print(f"Processed {processed_count} messages from SQS")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'OK',
            'processed_messages': processed_count
        })
    }
