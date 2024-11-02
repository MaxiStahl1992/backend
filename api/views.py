from django.http import JsonResponse
from .openai_service import get_openai_response
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import OpenAIModel, ChatMessage, ChatSession
from .enums import Temperature
from uuid import UUID

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
                {"role": msg.sender, "content": msg.content}
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
        messages = chat.messages.values("sender", "content", "timestamp", "model_name", "temperature")
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
