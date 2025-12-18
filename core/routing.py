from django.urls import path
from core.ws.consumers import HomeConsumer

websocket_urlpatterns = [
    path("ws/home/<int:home_id>/", HomeConsumer.as_asgi()),
]
