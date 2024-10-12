import traceback
from logging import getLogger

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management import BaseCommand

logger = getLogger("listener")

class Command(BaseCommand):

    help = "start listener"

    def handle(self, *args, **options):
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            p = r.pubsub()
            p.subscribe("main.dash_channel")
            channel_layer = get_channel_layer()
            for msg in p.listen():
                logger.debug(msg)
                if msg["type"] == "message":
                    m_type = "dash" if "dash" in msg["channel"] else "pool"
                    async_to_sync(channel_layer.group_send)(
                        "main",
                        {
                            "type": m_type,
                            "data": msg["data"]
                        }
                    )
        except Exception as ex:
            logger.exception(ex)
            logger.exception(traceback.format_exc())