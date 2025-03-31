import json
import os
import logging
import requests
from datetime import datetime, timedelta
from secretmanager import get_secret 
from auth_code_req import get_access_token

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

def handler(event, context):

    print('Notification received')
    print('Event:', event)

    query_params = event.get('queryStringParameters') or {}
    validation_token = query_params.get('validationToken')
    if validation_token:
        print('got validation token',validation_token)
        print('the type of validation token is',type(validation_token))
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': validation_token
        }

    print('Passed validation token')
 
    
    
    try:
        body = json.loads(event.get('body', '{}'))
        print("Parsed data:", body)
    except json.JSONDecodeError:
        body = {}
        print("Error parsing JSON body.")

    response_to_graph = {
        'statusCode': 200,
        'body': json.dumps({'status': 'Notification received'})
    }
   
    secret_name = os.environ.get('Secret_Name')
    region = os.environ.get('Region')

    secret = get_secret(secret_name,region)
    
    team_id = secret.get("team_id",None)
    channel_id = secret.get("channel_id",None)
    
    access_token = get_access_token(secret)    
    
    notifications = body.get("value", [])
    print("Received lifecycle notifications: %s", notifications)
    
    for notification in notifications:
        lifecycle_event = notification.get("lifecycleEvent")
        subscription_id = notification.get("subscriptionId")
        print("Processing event '%s' for subscription '%s'", lifecycle_event, subscription_id)
        
        if lifecycle_event == "reauthorizationRequired":
            reauthorize_subscription(subscription_id,access_token)
        # elif lifecycle_event == "subscriptionRemoved":
        #     recreate_subscription(subscription_id,team_id,channel_id,access_token)
        # elif lifecycle_event == "missed":
        #     process_missed_notifications(subscription_id)
        else:
            print("Unknown lifecycle event: %s", lifecycle_event)
            
    return response_to_graph

def reauthorize_subscription(subscription_id,access_token):
    print('entered reauthorize_subscription function')
    url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}/reauthorize"
    headers = {
        "Authorization": f"Bearer {access_token[0]}",
        "Content-Type": "application/json"
    }
    
    print("Calling reauthorize for subscription: %s", subscription_id)
    response = requests.post(url, headers=headers)
    if response.status_code in (200, 202):
        print("Subscription %s reauthorized successfully.", subscription_id)
    else:
        print("Failed to reauthorize subscription %s: %s", subscription_id, response.text)

# def recreate_subscription(subscription_id,team_id,channel_id,access_token):
#     notification_url = os.environ.get("Notification_URL")
#     lifecycle_notification_url = os.environ.get("LifeCycle_URL")
    
#     if not all([access_token, team_id, channel_id, notification_url]):
#         raise Exception("Missing one or more configuration environment variables")
    
#     expiration_datetime = (datetime.utcnow() + timedelta(minutes=55)).isoformat() + 'Z'
#     payload = {
#         "changeType": "created,updated",
#         "notificationUrl": notification_url,
#         "lifecycleNotificationUrl": lifecycle_notification_url,
#         "resource": f"/teams/{team_id}/channels/{channel_id}/messages",
#         "expirationDateTime": expiration_datetime,
#         "clientState": "SecretClient"
#     }
    
#     url = "https://graph.microsoft.com/v1.0/subscriptions"
#     headers = {
#         "Authorization": f"Bearer {access_token[0]}",
#         "Content-Type": "application/json"
#     }
    
#     print("Recreating subscription after removal of subscription: %s", subscription_id)
#     response = requests.post(url, json=payload, headers=headers)
#     if response.status_code in (200, 201):
#         logger.info("Subscription recreated successfully.")
#     else:
#         print("Failed to recreate subscription: %s", response.text)

# def process_missed_notifications(subscription_id):
#     """
#     Process a missed notifications lifecycle event. This is a placeholder where you can trigger a full data sync
#     (for example, by starting a delta query to fetch any changes that weren't delivered).
#     """
#     logger.info("Processing missed notifications for subscription: %s", subscription_id)
#     # Insert your custom logic to handle a full data sync here.
#     # For example, you might call a function or trigger another process.
#     pass