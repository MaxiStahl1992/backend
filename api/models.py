from django.db import models


class OpenAIModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    endpoint = models.CharField(max_length=255) 
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name