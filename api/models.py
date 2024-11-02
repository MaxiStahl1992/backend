from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class OpenAIModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    endpoint = models.CharField(max_length=255) 
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} - {self.title}"

class ChatMessage(models.Model):
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10)  # 'user' or 'ai'
    content = models.TextField()
    model_name = models.CharField(max_length=100)
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message in {self.chat} by {self.sender}"
