from secretmanager import get_secret 
from auth_code_req import get_access_token
import os, json, requests

def handler(event, context):
    try:
        # Retrieve environment variables for secrets
        secret_name = os.environ.get("Secret_Name")
        region = os.environ.get("Region")
        
        # Retrieve secret and access token
        secret = get_secret(secret_name, region)
        access_token = get_access_token(secret)
        
        # Setup the authorization header
        headers = {
            "Authorization": f"Bearer {access_token[0]}",
            "Content-Type": "application/json"
        }
        
        # Microsoft Graph API endpoint for subscriptions
        GRAPH_API_URL = "https://graph.microsoft.com/v1.0/subscriptions"
        
        # Fetch current subscriptions
        get_response = requests.get(GRAPH_API_URL, headers=headers)
        if get_response.status_code != 200:
            error_msg = f"Failed to fetch subscriptions: {get_response.status_code} {get_response.text}"
            print(error_msg)
            return {
                "statusCode": get_response.status_code,
                "body": json.dumps({"error": error_msg})
            }
        
        subscriptions = get_response.json().get("value", [])
        if not subscriptions:
            msg = "No subscriptions found to delete."
            print(msg)
            return {
                "statusCode": 200,
                "body": json.dumps({"message": msg})
            }
        
        deletion_results = []
        # Loop through each subscription and attempt deletion
        for subscription in subscriptions:
            sub_id = subscription.get("id")
            if not sub_id:
                deletion_results.append({"id": None, "status": "No subscription id found"})
                continue
            
            delete_url = f"{GRAPH_API_URL}/{sub_id}"
            del_response = requests.delete(delete_url, headers=headers)
            if del_response.status_code == 204:
                result = {"id": sub_id, "status": "deleted"}
                print(f"Subscription {sub_id} deleted successfully.")
            else:
                result = {"id": sub_id, "status": f"failed ({del_response.status_code})", "error": del_response.text}
                print(f"Failed to delete subscription {sub_id}: {del_response.status_code} {del_response.text}")
            deletion_results.append(result)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Deletion process completed.",
                "results": deletion_results
            })
        }
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_message})
        }
