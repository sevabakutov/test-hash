from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/telegram/main/$', consumers.PoolConsumer.as_asgi()),
]