from django.urls import path
from . import views

urlpatterns = [
    path("", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("app/", views.redirect_to_frontend, name="redirect_to_frontend"),
    path("api/generate-response/", views.generate_response, name="generate_response"),
    path("api/check-authentication/", views.check_authentication, name="check_authentication"),
    path("api/set-csrf-token/", views.set_csrf_token, name="set_csrf_token"),
    path("api/get-options/", views.get_options, name="get_options"),
    path('api/create-chat/', views.create_new_chat, name="create_new_chat"),
    path('api/chat-history/<uuid:chat_id>/', views.retrieve_chat_history, name="retrieve_chat_history"),
    path('api/delete-chat/<uuid:chat_id>/', views.delete_chat, name="delete_chat"),
    path("api/chats/", views.list_chats, name="list_chats"), 
    path("api/get-weather/", views.get_weather_data, name="get_weather_data"),
    path("api/stock/", views.get_stock_data, name="get_stock_data"),
]