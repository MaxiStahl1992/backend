from django.http import JsonResponse, HttpResponse
from .openai_service import get_openai_response
from django.conf import settings
from .enums import Temperature
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    print("This is the home view")
    return HttpResponse("Home!")


@login_required
def generate_response(request):
    """
    Django view that handles API requests,
    calls the Azure OpenAI API with a user-provided message,
    and returns the generated response in JSON format.

    Query Parameters:
        message (str): The message from the user.
        temperature (float): The sampling temperature (optional).
        model (str): The name of the model to use (optional).

    Returns:
        JsonResponse: JSON response containing the AI's reply or an error message.
    """
    user_message = request.GET.get("message", "Hello!")
    model_name = request.GET.get("model")
    temperature_str = request.GET.get("temperature")

    if temperature_str:
        try:
            temperature = Temperature(float(temperature_str)).value
        except ValueError:
            return JsonResponse({"error": "Invalid temperature value provided"}, status=400)
    else:
        temperature = None  # Pass None if not provided

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message},
        ]
        
        openai_response = get_openai_response(messages, temperature=temperature, model_name=model_name)
        return JsonResponse(openai_response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    