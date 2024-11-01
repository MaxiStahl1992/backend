import os
import requests
from django.conf import settings

def get_opai_response(prompt, engine='gpt-4o', temperature=0.7):
    headers = {
        "Authorization": f"Bearer {settings.AZURE_OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "prompt": prompt,
        "max_tokens": 100,
        "temperature": temperature,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }

    url = f"{settings.AZURE_OPENAI_API_URL}/{engine}/completions"

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return response.raise_for_status()