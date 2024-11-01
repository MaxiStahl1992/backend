from django.contrib import admin
from .models import OpenAIModel

@admin.register(OpenAIModel)
class OpenAIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'endpoint', 'description')
    filter = ('active')
    search_fields = ('name', 'description')
