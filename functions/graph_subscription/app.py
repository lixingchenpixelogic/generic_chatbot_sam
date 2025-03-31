from secretmanager import get_secret 
from auth_code_req import get_access_token
import os,json,requests
from datetime import datetime,timedelta

 
def handler(event,context):
    try:
        secret_name = os.environ.get('Secret_Name')
        region = os.environ.get('Region')
        notification_url = os.environ.get('Notification_URL')
        lifecycle_url = os.environ.get('LifeCycle_URL')
        print(' lifecycle_url looks like',lifecycle_url)

        print('secret_name looks like',secret_name,flush=True)
        secret = get_secret(secret_name,region)
        print('secret looks like',secret,flush=True)
        access_token = get_access_token(secret)
        
        team_id = secret.get("team_id",None)
        channel_id = secret.get("channel_id",None)

        expiration_datetime = (datetime.utcnow() + timedelta(minutes = 11)).isoformat() + 'Z'
        payload = {
            "changeType": "created,updated",
            "notificationUrl": notification_url,
            "lifecycleNotificationUrl":lifecycle_url,
            "resource": f"/teams/{team_id}/channels/{channel_id}/messages",
            "expirationDateTime": expiration_datetime,
            "clientState": "SecretClient"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token[0]}",
            "Content-Type": "application/json"
        }
        
        GRAPH_API_URL = "https://graph.microsoft.com/v1.0/subscriptions"

        response = requests.post(GRAPH_API_URL, json=payload, headers=headers)
        if response.status_code in (200, 201):
            print("Subscription created successfully.")
            return response.json()
        else:
            error_msg = f"Failed to subscribe: {response.status_code} {response.text}"
            print(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_message})
        }
    
    