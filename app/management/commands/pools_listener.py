import traceback
from logging import getLogger

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management import BaseCommand

logger = getLogger("listener.py")

class Command(BaseCommand):

    help = "start listener.py"

    def handle(self, *args, **options):
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            p = r.pubsub()
            p.subscribe("main.pools_channel")
            channel_layer = get_channel_layer()
            for msg in p.listen():
                logger.debug(msg)
                if msg["type"] == "message":
                    async_to_sync(channel_layer.group_send)(
                        "main",
                        {
                            "type": "pool",
                            "data": msg["data"]
                        }
                    )
        except Exception as ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())