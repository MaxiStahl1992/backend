from django.http import JsonResponse
from .openai_service import get_openai_response
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import OpenAIModel, ChatMessage, ChatSession
from .enums import Temperature
from uuid import UUID
import requests
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
@ensure_csrf_cookie
def generate_response(request):
    """
    Django view that handles API requests for generating responses from OpenAI.
    Requires a valid `chat_id`, `message`, `model`, and `temperature`.

    Expected JSON Payload:
        chat_id (str): The chat session ID.
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
        chat_id = data.get("chat_id")
        user_message = data.get("message")
        model_name = data.get("model")
        temperature = data.get("temperature")

        # Validate temperature
        try:
            temperature = float(temperature)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid temperature value provided"}, status=400)

        # Ensure chat_id is provided and valid
        if not chat_id:
            return JsonResponse({"error": "Chat ID is required"}, status=400)
        try:
            chat_uuid = UUID(chat_id) 
        except ValueError:
            return JsonResponse({"error": "Invalid chat ID format"}, status=400)

        # Ensure chat session exists
        try:
            chat = ChatSession.objects.get(id=chat_uuid, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Chat session not found"}, status=404)

        # Retrieve recent messages for context
        recent_messages = chat.messages.order_by("-timestamp")[:5]
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            *[
                {"role": msg.sender if msg.sender != "ai" else "assistant", "content": msg.content}
                for msg in reversed(recent_messages)
            ],
            {"role": "user", "content": user_message},
        ]

        # Call OpenAI API (using the helper function)
        openai_response = get_openai_response(messages, temperature=temperature, model_name=model_name)

        # Save user and AI messages to database
        ChatMessage.objects.create(
            chat=chat, sender="user", content=user_message, model_name=model_name, temperature=temperature
        )
        ai_reply = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        ChatMessage.objects.create(
            chat=chat, sender="ai", content=ai_reply, model_name=model_name, temperature=temperature
        )

        # Set chat title if it's the first message
        if not chat.title:
            chat.title = user_message[:30]
            chat.save()

        return JsonResponse({"content": ai_reply, "chat_id": chat_id})

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

@login_required
@require_POST
def create_new_chat(request):
    """
    Creates a new chat session and returns its ID.
    """
    chat = ChatSession.objects.create(user=request.user)
    return JsonResponse({"chat_id": str(chat.id)})

@login_required
def list_chats(request):
    """
    Lists all chat sessions for the current user.
    """
    user_chats = ChatSession.objects.filter(user=request.user).values("id", "title")
    chats = [{"chatId": str(chat["id"]), "chatTitle": chat["title"] or f"Chat {chat['id']}"} for chat in user_chats]
    return JsonResponse({"chats": chats})

@login_required
def retrieve_chat_history(request, chat_id):
    """
    Retrieves the chat history for a specific chat session.
    """
    try:
        chat = ChatSession.objects.get(id=chat_id, user=request.user)
        messages = chat.messages.filter(regenerated=False).values("sender", "content", "timestamp", "model_name", "temperature")
        return JsonResponse({"messages": list(messages)})
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Chat session not found"}, status=404)

@login_required
@require_POST
def delete_chat(request, chat_id):
    """
    Deletes a chat session and all its associated messages.
    If no more chats exist, creates a new empty chat session.
    """
    try:
        chat = ChatSession.objects.get(id=chat_id, user=request.user)
        chat.delete()

        # Check if any remaining chat sessions exist; if none, create a new one
        if not ChatSession.objects.filter(user=request.user).exists():
            new_chat = ChatSession.objects.create(user=request.user)
            new_chat_id = str(new_chat.id)
        else:
            new_chat_id = None

        return JsonResponse({
            "detail": "Chat deleted successfully.",
            "new_chat_id": new_chat_id,
        })
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Chat session not found"}, status=404)

@require_POST
@login_required
def regenerate_message(request, chat_id):
    """
    Marks the last AI message as "regenerated" and re-fetches a response based on the last user message
    and the previous five messages as context.
    """
    # Retrieve the chat session
    chat = get_object_or_404(ChatSession, id=chat_id, user=request.user)

    # Find the last AI message and mark it as regenerated
    last_ai_message = chat.messages.filter(sender="ai", regenerated=False).order_by("-timestamp").first()
    if not last_ai_message:
        return JsonResponse({"error": "No AI message to regenerate."}, status=400)
    last_ai_message.regenerated = True
    last_ai_message.save()

    # Retrieve recent messages, excluding those marked for regeneration
    recent_messages = chat.messages.filter(regenerated=False).order_by("-timestamp")[:5]
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        *[
            {"role": msg.sender if msg.sender != "ai" else "assistant", "content": msg.content}
            for msg in reversed(recent_messages)
        ]
    ]

    # Use the last user message as the final prompt
    last_user_message = next((msg for msg in reversed(recent_messages) if msg.sender == "user"), None)
    if last_user_message:
        messages.append({"role": "user", "content": last_user_message.content})
    else:
        return JsonResponse({"error": "No user message found for regeneration."}, status=400)

    # Generate a new AI response based on the last user message and recent context
    try:
        openai_response = get_openai_response(messages, temperature=last_user_message.temperature, model_name=last_user_message.model_name)
        regenerated_content = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Save the new AI message in the database
        new_ai_message = ChatMessage.objects.create(
            chat=chat,
            sender="ai",
            content=regenerated_content,
            model_name=last_user_message.model_name,
            temperature=last_user_message.temperature,
            timestamp=timezone.now(),
        )

        return JsonResponse({"content": new_ai_message.content})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Weather API
@require_GET
def get_weather_data(request):
    # Retrieve latitude and longitude from query parameters
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    
    # Check if coordinates are provided
    if not latitude or not longitude:
        return JsonResponse({"error": "Latitude and longitude are required"}, status=400)

    # Set up Open-Meteo API endpoint with desired parameters
    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )

    try:
        # Make request to Open-Meteo API
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json().get("current_weather", {})
        
        # Structure the response data
        data = {
            "temperature": weather_data.get("temperature"),
            "windspeed": weather_data.get("windspeed"),
            "winddirection": weather_data.get("winddirection"),
            "weathercode": weather_data.get("weathercode"),
            "time": weather_data.get("time"),
        }

        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": "Failed to fetch weather data"}, status=500)

