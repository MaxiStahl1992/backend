from django.db import models
from django.conf import settings
from uuid import uuid4

class OpenAIModel(models.Model):
    """
    Represents an OpenAI model configuration.

    Attributes:
        name (str): The unique name of the model.
        endpoint (str): The endpoint URL for the model.
        description (str): Optional description of the model.
        active (bool): Indicates whether the model is active.
    """
    name = models.CharField(max_length=100, unique=True)
    endpoint = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ChatSession(models.Model):
    """
    Represents a chat session between a user and the AI assistant.

    Attributes:
        id (UUID): The unique identifier for the chat session.
        user (User): The user associated with the chat session.
        title (str): The title of the chat session.
        created_at (datetime): The timestamp when the chat was created.
        last_updated (datetime): The timestamp when the chat was last updated.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} - {self.title}"

class ChatMessage(models.Model):
    """
    Represents a message in a chat session.

    Attributes:
        chat (ChatSession): The chat session this message belongs to.
        sender (str): The sender of the message ('user' or 'ai').
        content (str): The content of the message.
        model_name (str): The name of the OpenAI model used.
        temperature (float): The temperature setting for the response.
        regenerated (bool): Indicates if the message was regenerated.
        timestamp (datetime): The timestamp when the message was created.
    """
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    model_name = models.CharField(max_length=100)
    temperature = models.FloatField()
    regenerated = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message in {self.chat} by {self.sender}"