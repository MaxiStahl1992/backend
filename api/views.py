import json
import logging
from uuid import UUID

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ChatMessage, ChatSession, OpenAIModel
from .openai_service import get_openai_response

logger = logging.getLogger(__name__)

def redirect_to_frontend(request):
    """
    Redirects the user to the frontend application.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponseRedirect: A redirect to the frontend URL.
    """
    return redirect("http://localhost:5173")

@ensure_csrf_cookie
def set_csrf_token(request):
    """
    Sets the CSRF token cookie.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response indicating the CSRF token is set.
    """
    return JsonResponse({"detail": "CSRF cookie set"})

@login_required
def check_authentication(request):
    """
    Checks if the user is authenticated.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response indicating authentication status.
    """
    return JsonResponse({"isAuthenticated": True})

@login_required
@require_POST
@ensure_csrf_cookie
def generate_response(request):
    """
    Generates a response from the AI assistant based on the user's message.

    Expects a JSON payload with 'chat_id', 'message', 'model', and 'temperature'.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response containing the AI's reply or an error message.
    """
    try:
        data = json.loads(request.body)
        chat_id = data.get("chat_id")
        user_message = data.get("message")
        model_name = data.get("model")
        temperature = data.get("temperature")

        if not all([chat_id, user_message, model_name, temperature]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            temperature = float(temperature)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid temperature value provided"}, status=400)

        try:
            chat_uuid = UUID(chat_id)
        except ValueError:
            return JsonResponse({"error": "Invalid chat ID format"}, status=400)

        chat = get_object_or_404(ChatSession, id=chat_uuid, user=request.user)

        recent_messages = chat.messages.order_by("-timestamp")[:5]
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            *[
                {"role": "assistant" if msg.sender == "ai" else msg.sender, "content": msg.content}
                for msg in reversed(recent_messages)
            ],
            {"role": "user", "content": user_message},
        ]

        openai_response = get_openai_response(messages, temperature=temperature, model_name=model_name)

        ai_reply = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")

        ChatMessage.objects.create(
            chat=chat, sender="user", content=user_message, model_name=model_name, temperature=temperature
        )
        ChatMessage.objects.create(
            chat=chat, sender="ai", content=ai_reply, model_name=model_name, temperature=temperature
        )

        if not chat.title:
            chat.title = user_message[:30]
            chat.save()

        return JsonResponse({"content": ai_reply, "chat_id": chat_id})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception:
        logger.exception("Error generating response")
        return JsonResponse({"error": "An error occurred while generating the response."}, status=500)

@login_required
def get_options(request):
    """
    Retrieves available models and temperature options.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response containing models and temperatures.
    """
    models = OpenAIModel.objects.filter(active=True).values_list("name", flat=True)
    temperatures = [0.2, 0.7, 0.9]
    return JsonResponse({
        "models": list(models),
        "temperatures": temperatures
    })

@login_required
@require_POST
def create_new_chat(request):
    """
    Creates a new chat session.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response containing the new chat ID.
    """
    chat = ChatSession.objects.create(user=request.user)
    return JsonResponse({"chat_id": str(chat.id)})

@login_required
def list_chats(request):
    """
    Lists all chat sessions for the current user.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response containing a list of chats.
    """
    user_chats = ChatSession.objects.filter(user=request.user).values("id", "title")
    chats = [{"chatId": str(chat["id"]), "chatTitle": chat["title"] or f"Chat {chat['id']}"} for chat in user_chats]
    return JsonResponse({"chats": chats})

@login_required
def retrieve_chat_history(request, chat_id):
    """
    Retrieves the chat history for a specific chat session.

    Args:
        request (HttpRequest): The incoming HTTP request.
        chat_id (UUID): The ID of the chat session.

    Returns:
        JsonResponse: A JSON response containing the chat messages.
    """
    chat = get_object_or_404(ChatSession, id=chat_id, user=request.user)
    messages = chat.messages.filter(regenerated=False).values(
        "sender", "content", "timestamp", "model_name", "temperature"
    )
    return JsonResponse({"messages": list(messages)})

@login_required
@require_POST
def delete_chat(request, chat_id):
    """
    Deletes a chat session and its associated messages.

    If no more chats exist, creates a new empty chat session.

    Args:
        request (HttpRequest): The incoming HTTP request.
        chat_id (UUID): The ID of the chat session to delete.

    Returns:
        JsonResponse: A JSON response indicating success and a new chat ID if applicable.
    """
    chat = get_object_or_404(ChatSession, id=chat_id, user=request.user)
    chat.delete()

    if not ChatSession.objects.filter(user=request.user).exists():
        new_chat = ChatSession.objects.create(user=request.user)
        new_chat_id = str(new_chat.id)
    else:
        new_chat_id = None

    return JsonResponse({
        "detail": "Chat deleted successfully.",
        "new_chat_id": new_chat_id,
    })

@login_required
@require_POST
def regenerate_message(request, chat_id):
    """
    Regenerates the last AI message in a chat session.

    Marks the last AI message as regenerated and generates a new response.

    Args:
        request (HttpRequest): The incoming HTTP request.
        chat_id (UUID): The ID of the chat session.

    Returns:
        JsonResponse: A JSON response containing the new AI message content.
    """
    chat = get_object_or_404(ChatSession, id=chat_id, user=request.user)

    last_ai_message = chat.messages.filter(sender="ai", regenerated=False).order_by("-timestamp").first()
    if not last_ai_message:
        return JsonResponse({"error": "No AI message to regenerate."}, status=400)
    last_ai_message.regenerated = True
    last_ai_message.save()

    recent_messages = chat.messages.filter(regenerated=False).order_by("-timestamp")[:5]
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        *[
            {"role": "assistant" if msg.sender == "ai" else msg.sender, "content": msg.content}
            for msg in reversed(recent_messages)
        ]
    ]

    last_user_message = next((msg for msg in reversed(recent_messages) if msg.sender == "user"), None)
    if last_user_message:
        messages.append({"role": "user", "content": last_user_message.content})
    else:
        return JsonResponse({"error": "No user message found for regeneration."}, status=400)

    try:
        openai_response = get_openai_response(
            messages,
            temperature=last_user_message.temperature,
            model_name=last_user_message.model_name
        )
        regenerated_content = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")

        ChatMessage.objects.create(
            chat=chat,
            sender="ai",
            content=regenerated_content,
            model_name=last_user_message.model_name,
            temperature=last_user_message.temperature,
            timestamp=timezone.now(),
        )

        return JsonResponse({"content": regenerated_content})
    except Exception:
        logger.exception("Error regenerating message")
        return JsonResponse({"error": "An error occurred while regenerating the message."}, status=500)

@require_GET
def get_weather_data(request):
    """
    Retrieves current weather data based on latitude and longitude.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: A JSON response containing weather data or an error message.
    """
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    
    if not latitude or not longitude:
        return JsonResponse({"error": "Latitude and longitude are required"}, status=400)

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )

    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json().get("current_weather", {})
        
        data = {
            "temperature": weather_data.get("temperature"),
            "windspeed": weather_data.get("windspeed"),
            "winddirection": weather_data.get("winddirection"),
            "weathercode": weather_data.get("weathercode"),
            "time": weather_data.get("time"),
        }

        return JsonResponse(data)
    except requests.exceptions.RequestException:
        logger.exception("Failed to fetch weather data")
        return JsonResponse({"error": "Failed to fetch weather data"}, status=500)
    