from django.urls import path
from . import views

urlpatterns = [
    path("", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("app/", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("generate-response/", views.generate_response, name="generate_response"),
    path("check-authentication/", views.check_authentication, name="check_authentication"),
]