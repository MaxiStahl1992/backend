import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .models import OpenAIModel

logger = logging.getLogger(__name__)

def get_openai_response(messages, temperature=0.7, model_name=None):
    """
    Sends messages to the OpenAI API and retrieves the response.

    Args:
        messages (list): List of message dictionaries for the conversation.
        temperature (float): The sampling temperature for the AI model.
        model_name (str): The name of the OpenAI model to use.

    Returns:
        dict: The response from the OpenAI API.

    Raises:
        ValueError: If the specified model does not exist or is inactive.
        ImproperlyConfigured: If required settings are missing.
        RequestException: If the API request fails.
    """
    if temperature is None:
        temperature = 0.7

    if model_name:
        try:
            model = OpenAIModel.objects.get(name=model_name, active=True)
        except OpenAIModel.DoesNotExist:
            raise ValueError("The specified model does not exist or is inactive.")
    else:
        model = OpenAIModel.objects.filter(active=True).first()
        if not model:
            raise ValueError("No active models are available in the database. Please configure a model.")

    azure_openai_endpoint = getattr(settings, 'AZURE_OPENAI_ENDPOINT', None)
    azure_openai_api_key = getattr(settings, 'AZURE_OPENAI_API_KEY', None)

    if not azure_openai_endpoint or not azure_openai_api_key:
        raise ImproperlyConfigured("Azure OpenAI settings are not properly configured.")

    url = f"{azure_openai_endpoint}/openai/deployments/{model.endpoint}/chat/completions?api-version=2024-06-01"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_api_key,
    }
    data = {
        "messages": messages,
        "temperature": temperature,
    }
    
    logger.debug("Request URL: %s", url)
    logger.debug("Payload: %s", data)

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.debug("API Response: %s", response.json())
        return response.json()
    except requests.exceptions.RequestException:
        logger.exception("OpenAI API request failed")
        raise