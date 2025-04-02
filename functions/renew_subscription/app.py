import json
import os
import logging
import requests
from datetime import datetime, timedelta
from secretmanager import get_secret 
from auth_code_req import get_access_token
import boto3

def handler(event, context):
    print("RenewSubscriptionFunction received event:", event)
    
    if "body" in event:
        try:
            body = json.loads(event.get("body", "{}"))
        except Exception as e:
            print("Error parsing event body:", str(e))
            body = {}
    else:
        body = event

    secret_name = os.environ.get('Secret_Name')
    region = os.environ.get('Region')
    secret = get_secret(secret_name, region)
    access_token = get_access_token(secret)
    
    notifications = body.get("value", [])
    print("Processing lifecycle notifications:", notifications)
    
    for notification in notifications:
        subscription_id = notification.get("subscriptionId")
        lifecycle_event = notification.get("lifecycleEvent")
        print("Processing event '%s' for subscription '%s'" % (lifecycle_event, subscription_id))
        
        if lifecycle_event == "reauthorizationRequired":
            new_expiration = (datetime.utcnow() + timedelta(minutes = 45)).isoformat() + 'Z'
            payload = {
                "expirationDateTime": new_expiration
            }
            url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
            headers = {
                "Authorization": f"Bearer {access_token[0]}",
                "Content-Type": "application/json"
            }
            
            print(f"Calling PATCH to renew subscription {subscription_id} with expiration {new_expiration}")
            try:
                response = requests.patch(url, json=payload, headers=headers)
                if response.status_code == 200:
                    print(f"Subscription {subscription_id} renewed successfully.")
                else:
                    print(f"Failed to renew subscription {subscription_id}: {response.status_code} {response.text}")
                    try:
                        print(f"Attempting to delete subscription {subscription_id}.")
                        delete_response = requests.delete(url, headers=headers)
                        if delete_response.status_code in [200, 204]:
                            print(f"Subscription {subscription_id} deleted successfully.")
                        else:
                            print(f"Failed to delete subscription {subscription_id}: {delete_response.status_code} {delete_response.text}")
                    except Exception as delete_exception:
                        print(f"Exception while deleting subscription {subscription_id}: {str(delete_exception)}")
                    
                    lambda_client = boto3.client('lambda')
                    lambda_client.invoke(
                        FunctionName=os.environ.get('New_Subscription_Name'),
                        InvocationType='Event'
                    )
                    print('Invoking a new subscription')
            except Exception as e:
                print(f"Error during renew_subscription for {subscription_id}: {str(e)}")
        elif lifecycle_event == "subscriptionRemoved":
            print(f"Subscription {subscription_id} has been removed.")
        else:
            print("Unknown lifecycle event: %s" % lifecycle_event)
            
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'Renewal complete'})
    }
    
# import json
# import os
# import logging
# import threading
# import requests
# from datetime import datetime, timedelta
# from secretmanager import get_secret 
# from auth_code_req import get_access_token

# def handler(event, context):
#     print('Notification received')
#     print('Event:', event)

#     query_params = event.get('queryStringParameters') or {}
#     validation_token = query_params.get('validationToken')
#     if validation_token:
#         print('Got validation token', validation_token)
#         return {
#             'statusCode': 200,
#             'headers': {'Content-Type': 'text/plain'},
#             'body': validation_token
#         }

#     try:
#         body = json.loads(event.get('body', '{}'))
#         print("Parsed data:", body)
#     except json.JSONDecodeError:
#         body = {}
#         print("Error parsing JSON body.")

#     # Respond immediately to Graph API to stop retrying
#     response_to_graph = {
#         'statusCode': 200,
#         'body': json.dumps({'status': 'Notification received'})
#     }
   
#     secret_name = os.environ.get('Secret_Name')
#     region = os.environ.get('Region')

#     secret = get_secret(secret_name, region)
#     team_id = secret.get("team_id")
#     channel_id = secret.get("channel_id")
#     access_token = get_access_token(secret)    
    
#     notifications = body.get("value", [])
#     print("Received lifecycle notifications:", notifications)
    
#     # Process notifications asynchronously
#     for notification in notifications:
#         lifecycle_event = notification.get("lifecycleEvent")
#         subscription_id = notification.get("subscriptionId")
#         print("Processing event '%s' for subscription '%s'" % (lifecycle_event, subscription_id))
        
#         if lifecycle_event == "reauthorizationRequired":
#             # Spawn a background thread to handle the renewal
#             thread = threading.Thread(target=renew_subscription, args=(subscription_id, access_token))
#             thread.start()
#         else:
#             print("Unknown lifecycle event: %s" % lifecycle_event)
            
#     return response_to_graph

# def renew_subscription(subscription_id, access_token):
#     # Calculate new expiration time (e.g., 11 minutes from now)
#     new_expiration = (datetime.utcnow() + timedelta(minutes=11)).isoformat() + 'Z'
#     payload = {
#         "expirationDateTime": new_expiration
#     }
#     url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"
#     headers = {
#         "Authorization": f"Bearer {access_token[0]}",
#         "Content-Type": "application/json"
#     }
    
#     print(f"Calling PATCH to renew subscription {subscription_id} with expiration {new_expiration}")
#     try:
#         response = requests.patch(url, json=payload, headers=headers)
#         if response.status_code == 200:
#             print(f"Subscription {subscription_id} renewed successfully.")
#         else:
#             print(f"Failed to renew subscription {subscription_id}: {response.status_code} {response.text}")
#     except Exception as e:
#         print(f"Error during renew_subscription for {subscription_id}: {str(e)}")
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