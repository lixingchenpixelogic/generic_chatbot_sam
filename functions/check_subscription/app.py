from secretmanager import get_secret 
from auth_code_req import get_access_token
import os, json, requests

def handler(event, context):
    try:
        # Retrieve necessary environment variables
        secret_name = os.environ.get('Secret_Name')
        region = os.environ.get('Region')
        
        print('secret_name looks like', secret_name, flush=True)
        secret = get_secret(secret_name, region)
        access_token = get_access_token(secret)
        
        # Setup headers with the access token from your secret
        headers = {
            "Authorization": f"Bearer {access_token[0]}",
            "Content-Type": "application/json"
        }
        
        # Microsoft Graph API endpoint for subscriptions
        GRAPH_API_URL = "https://graph.microsoft.com/v1.0/subscriptions"
        
        # Make the GET request to fetch the current subscriptions
        response = requests.get(GRAPH_API_URL, headers=headers)
        
        if response.status_code == 200:
            print("Fetched subscriptions successfully.")
            # Return the subscription data
            return {
                "statusCode": 200,
                "body": response.json()
            }
        else:
            error_msg = f"Failed to fetch subscriptions: {response.status_code} {response.text}"
            print(error_msg)
            return {
                "statusCode": response.status_code,
                "body": {"error": error_msg}
            }
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return {
            "statusCode": 500,
            "body": {"error": error_message}
        }