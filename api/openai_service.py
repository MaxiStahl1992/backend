import requests
from django.conf import settings
from .models import OpenAIModel
from .enums import Temperature

def get_openai_response(messages, temperature=0.7, model_name="gpt-4o"):
    """
    Sends a prompt to the Azure OpenAI API and returns the generated response.

    Parameters:
        messages (list): List of message objects in the format [{"role": "user", "content": "message"}].
        temperature (float): Sampling temperature to control randomness in the output. Defaults to Temperature.MEDIUM.
        model_name (str): Name of the model to use, as stored in the database. Defaults to the first active model in the database.

    Returns:
        dict: JSON response from the Azure OpenAI API if the request is successful.

    Raises:
        HTTPError: If the API request fails.
        ValueError: If the specified model does not exist or is inactive. Or if no active models are available in the database.
    """
    if temperature is None:
        temperature = Temperature.MEDIUM.value

    if model_name:
        try:
            model = OpenAIModel.objects.get(name=model_name, active=True)
        except OpenAIModel.DoesNotExist:
            raise ValueError(f"The specified model does not exist or is inactive.")
    else:
        model = OpenAIModel.objects.filter(active=True).first()
        if not model:
            raise ValueError("No active models are available in the database. Please configure a model.")

    # Construct the API request using the model endpoint
    url = f"{settings.AZURE_OPENAI_ENDPOINT}{model.endpoint}"
    headers = {
        "Content-Type": "application/json",
        "api-key": settings.AZURE_OPENAI_API_KEY,
    }
    data = {
        "messages": messages,
        "temperature": temperature,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"OpenAI API request failed: {e}")
        raise
