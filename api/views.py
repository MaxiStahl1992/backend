from django.http import JsonResponse
from .openai_service import get_openai_response
from django.conf import settings
from .enums import Temperature
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import OpenAIModel
from .enums import Temperature

def redirect_to_frontend(request):
    return redirect("http://localhost:5173") 

@ensure_csrf_cookie
def set_csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set"})

@login_required
def check_authentication(request):
    return JsonResponse({"isAuthenticated": True})

@login_required
@require_POST
def generate_response(request):
    """
    Django view that handles API requests,
    calls the Azure OpenAI API with a user-provided message,
    and returns the generated response in JSON format.

    Expected JSON Payload:
        message (str): The message from the user.
        temperature (float, optional): The sampling temperature.
        model (str, optional): The name of the model to use.

    Returns:
        JsonResponse: JSON response containing the AI's reply or an error message.
    """
    if request.session.get("is_processing"):
        return JsonResponse({"error": "Another request is already in progress"}, status=400)
    
    request.session["is_processing"] = True
    try:
        # Parse JSON payload
        data = json.loads(request.body)
        user_message = data.get("message")
        model_name = data.get("model")  
        temperature = data.get("temperature") 

        # Ensure temperature is a valid float
        try:
            temperature = float(temperature)
        except ValueError:
            return JsonResponse({"error": "Invalid temperature value provided"}, status=400)

        # Create message history
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message},
        ]
        
        # Call OpenAI API (your helper function)
        openai_response = get_openai_response(messages, temperature=temperature, model_name=model_name)
        return JsonResponse(openai_response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    finally:
        request.session["is_processing"] = False


@login_required
def get_options(request):
    """
    Django view that returns the available models and temperature options.

    Returns:
        JsonResponse: JSON response containing the available models and temperature options.
    """
    models = OpenAIModel.objects.filter(active=True).values_list("name", flat=True)
    temperatures = [temperature.value for temperature in Temperature]
    return JsonResponse({
        "models": list(models),
        "temperatures": temperatures
    })
