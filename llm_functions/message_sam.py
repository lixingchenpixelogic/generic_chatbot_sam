from auth_code_req import get_access_token_username
import requests
from secretmanager import get_secret
from ai_bot_deepseek import get_ai_response_deepseek
from ai_bot_llama import get_ai_response_llama


def post_response_to_message(team_id, channel_id, message_id, response_content, secret):

    access_token_username = get_access_token_username(secret)

    url = f'https://graph.microsoft.com/beta/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies'
 
    headers = {
        'Authorization': f'Bearer {access_token_username[0]}',
        'Content-Type': 'application/json'
    }
    data = {
        'body': {
            'content': response_content
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        reply_data = response.json()
        print('reply_data looks like',reply_data)
        reply_id = reply_data.get('id')
        return reply_id
        
    except Exception as e:
        print(f"Error posting reply: {e}")
        return None
    


def update_response(team_id, channel_id, message_id, reply_id, llm_response, secret):

    access_token = get_access_token_username(secret)

    url = f'https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies/{reply_id}'
    headers = {
        'Authorization': f'Bearer {access_token[0]}',
        'Content-Type': 'application/json'
    }
    data = {
        'body': {
            'content': llm_response
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.status_code


def process_message_with_llm(content):
    # if "deepseek" in content:
    #     generated_response = get_ai_response_deepseek(content)
    #     return f"Here is your deepseek generated response: {generated_response}"
    # elif "llama" in content:
    #     generated_response = get_ai_response_llama(content)
    #     return f"Here is your llama generated response: {generated_response}"
    # else:
    #     print('got into else')
    #     generated_response = get_ai_response_llama(content)
    #     return f"{generated_response}"
        generated_response = get_ai_response_deepseek(content)
        return f"Here is your deepseek generated response: {generated_response}"
    
if __name__ == "__main__":
    # https://teams.microsoft.com/l/message/19:7dbbb37efaf040ae9772d5f207777fc7@thread.tacv2/1743010508384?tenantId=424a7d93-d185-47d0-87bc-0dd80b211d5d&groupId=aca6c727-c2d7-4761-9a93-1f00e3b06a3b&parentMessageId=1743010508384&teamName=PixelBot&channelName=Generic&createdTime=1743010508384
    payload = {
        'message_id' : '1743010508384',
        'content' :'Translate cuantos anos tu eres to English',
        'title' : 'Please translate the following thing'       
    }
    secret_name = 'pixelbot-chatbot-dev'
    region = 'us-east-1'
    secret = get_secret(secret_name, region)
    team_id = secret.get("team_id",None)
    channel_id = secret.get("channel_id",None)
    message_id = payload.get('message_id',None)
    title = payload.get('title',None)
    content = payload.get('content',None)
    reply_id = post_response_to_message(team_id,channel_id,message_id,'Waiting for LLM to respond',secret)
    print('reply id looks like',reply_id)
    llm_response = process_message_with_llm(content)
    print('llm_response looks like',llm_response)
    update_response(team_id, channel_id, message_id, reply_id, llm_response, secret)
    