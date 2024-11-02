from django.urls import path
from . import views

urlpatterns = [
    path("", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("app/", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("api/generate-response/", views.generate_response, name="generate_response"),
    path("api/check-authentication/", views.check_authentication, name="check_authentication"),
    path("api/set-csrf-token/", views.set_csrf_token, name="set_csrf_token"),
    path("api/get-options/", views.get_options, name="get_options"),
]