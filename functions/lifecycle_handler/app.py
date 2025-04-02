import json
import os
import logging
import boto3

def handler(event, context):
    print('Notification received')
    print('Event:', event)

    query_params = event.get('queryStringParameters') or {}
    validation_token = query_params.get('validationToken')
    if validation_token:
        print('Got validation token', validation_token)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': validation_token
        }
    
    print("Invoking RenewSubscriptionFunction asynchronously with payload:", event)
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=os.environ.get('Renew_Function_Name'),
        InvocationType='Event',
        Payload=json.dumps(event)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'Notification received'})
    }