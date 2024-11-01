from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("generate-response/", views.generate_response, name="generate_response"),
]