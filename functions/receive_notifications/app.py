import json
import os
import requests
import threading
from secretmanager import get_secret 
from auth_code_req import get_access_token
 
CLIENT_STATE = "SecretClient"

def process_notifications(event):
    """Processes the notifications asynchronously."""
    print('started processing asyncronously')
    secret_name = os.environ.get('Secret_Name')
    region = os.environ.get('Region')
    secret = get_secret(secret_name, region)
    team_id = secret.get("team_id", None)
    channel_id = secret.get("channel_id", None)
    access_token = get_access_token(secret)
    
    try:
        data = json.loads(event.get('body', '{}'))
        print("Parsed data:", data)
    except json.JSONDecodeError:
        data = {}
        print("Error parsing JSON body.")
    
    if data and "value" in data:
        for notification in data["value"]:
            if notification.get("clientState") == CLIENT_STATE:
                print("Notification received with change type:", notification.get("changeType"))
                resource_data = notification.get("resourceData")
                if resource_data:
                    message_id = resource_data.get("id")
                    if message_id:
                        print("Extracted Message ID from resourceData:", message_id)
                    else:
                        print("Message ID not found in resourceData.")
                        continue
                else:
                    print("No resourceData available in the notification.")
                    continue

                graph_url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages/{message_id}"
                headers = {
                    "Authorization": f"Bearer {access_token[0]}",
                    "Content-Type": "application/json"
                }
                response = requests.get(graph_url, headers=headers)
                if response.status_code == 200:
                    message_details = response.json()
                    title = message_details.get("subject", "No title available")
                    body_content = message_details.get("body", {}).get("content", "No content available")
                    print("Message Title:", title)
                    print("Message Content:", body_content)
                else:
                    print("Failed to retrieve message details. Status code:", response.status_code)
            else:
                print("Invalid clientState received.")
    else:
        print("No valid data received in notification.")

def handler(event, context):
    print('Notification received')
    print('Event:', event)
    
    # Handle validation token quickly (this is necessary for subscription validation)
    query_params = event.get('queryStringParameters') or {}
    validation_token = query_params.get('validationToken')
    if validation_token:
        print('Got validation token:', validation_token)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': validation_token
        }
    
    # Create the immediate acknowledgment response
    ack_response = {
        'statusCode': 200,
        'body': json.dumps({'status': 'Notification received'})
    }
    
    # Start processing the notification asynchronously in a background thread
    threading.Thread(target=process_notifications, args=(event,)).start()
    
    # Return the acknowledgment immediately to ensure fast HTTP response
    return ack_response