import re
import pandas as pd
import openai, os, argparse

__version__ = "1.0.1"

os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_BASE_URL"] = "http://10.100.10.178:11434/v1"

__openai_api_key__ = os.getenv("OPENAI_API_KEY")
__openai_base_url__ = os.getenv("OPENAI_BASE_URL")
__openai_model__ = "llama3.1:8b"

if not __openai_api_key__:
    raise Exception("Missing env: OPENAI_API_KEY")

def get_ai_response_llama(prompt):
    try:
        client = openai.Client()

        response = client.chat.completions.create(
            model=__openai_model__,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Do not include any explanations. Do not include any <p> or </p> tags. "},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        raw_response = response.choices[0].message.content.strip()

        removed_think_response = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()

        return removed_think_response
    
    except Exception as e:
        return f"Error: {e}"