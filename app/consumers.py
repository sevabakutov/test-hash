import json
import logging
from urllib.parse import parse_qsl

import redis
from asgiref.sync import sync_to_async
from redis.exceptions import DataError

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from app.models import TelegramUser, TradeIdea, TradeInvestment
from app.serializers import TelegramUserSerializer, TradingPoolSerializer, TradeInvestmentSerializer
from app.utils import verify_telegram_init_data

logger = logging.getLogger("channels")

redis_client1 = redis.Redis(host='localhost', port=6379, decode_responses=True)

class PoolConsumer(AsyncWebsocketConsumer):

    @classmethod
    def set_active(cls, key: str | int, value: str) -> None:
        redis_client1.hset("actives", key, value)

    @classmethod
    def update_dashboard(cls, key: str, value: int) -> None:
        redis_client1.zadd("dashboard", {key: value})
        redis_client1.publish(
            "main.dash_channel",
            json.dumps(redis_client1.zrange("dashboard", 0, -1, withscores=True))
        )

    @classmethod
    def load_dashboard(cls):
        return json.dumps(redis_client1.zrange("dashboard", 0, -1, withscores=True))

    @classmethod
    def delete_user_from_dashboard(cls, key: str) -> None:
        redis_client1.zrem("dashboard", key)
        redis_client1.publish(
            "main.dash_channel",
            json.dumps(redis_client1.zrange("dashboard", 0, -1, withscores=True))
        )

    @database_sync_to_async
    def db_user_create(self, username: str) -> TelegramUser:
        return TelegramUser.objects.create(username=username, pnl=0)
    @database_sync_to_async
    def db_user_get(self, username: str) -> TelegramUser:
        return TelegramUser.objects.get(username=username)
    @database_sync_to_async
    def db_user_trade_pools(self, user: TelegramUser):
        trade_pools = TradeIdea.objects.filter(user=user)
        ser = TradingPoolSerializer(trade_pools, many=True)
        return ser.data
    @database_sync_to_async
    def db_user_trade_invs(self, user: TelegramUser):
        trade_invs = TradeInvestment.objects.filter(user=user)
        ser = TradeInvestmentSerializer(trade_invs, many=True)
        return ser.data
    @database_sync_to_async
    def db_make_action(self, action: str, obj=object) -> None:
        if action == "delete":
            obj.delete()
        elif action == "save":
            obj.save()
    @database_sync_to_async
    def db_check_user(self, username):
        return TelegramUser.objects.filter(username=username).exists()


    async def connect(self):
        self.room_group_name = "main"

        logger.info(f"WebSocket connection established: {self.channel_name} to group {self.room_group_name}")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()


    async def disconnect(self, code):
        logger.info(f"WebSocket disconnected: {self.channel_name} from group {self.room_group_name} with code {code}")

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        m_type = data["type"]
        action = data["action"]
        params = data["params"]

        # Active type
        if m_type == "active":
            if action == "get":
                await self.get_active(params["key"])

        # User type
        elif m_type == "user":
            if action == "auth":
                user_data = await self.verif(params["init_data"])
                username = user_data["username"]
                if await self.db_check_user(username):
                    await self.user_get_all_data(username)
                    leaderboard = json.loads(self.load_dashboard())
                    await self.send(text_data=json.dumps({
                        "type": "dash",
                        "data": leaderboard[-3:][::-1]
                    }))

                else:
                    await self.user_create(username)
                    await self.user_get_all_data(username)
                    self.update_dashboard(username, 0)
            else:
                username = params["username"]
                if action == "update":
                    pnl = params.get("pnl")
                    if pnl is not None:
                        self.update_dashboard(username, pnl)
                    await self.user_update(username, params.get("wallet"), pnl)
                    await self.user_get_data(username)

                elif action == "delete":
                    await self.user_destroy(username)
                    self.delete_user_from_dashboard(username)

                elif action == "get":
                    await self.user_get_data(username)

        # elif m_type == "dash":
        #     await self.get_dashboard()


    async def verif(self, init_data_str: str) -> dict:
        init_data = dict(parse_qsl(init_data_str))

        if verify_telegram_init_data(init_data):
            return json.loads(init_data.get('user', '{}'))

        else:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Some problems with user verification"
            }))

    async def dash(self, event):
        data = event['data']
        data = json.loads(data)
        logger.info(f"Dashboard update received: {data}")

        # Отправка сообщения клиенту напрямую
        await self.send(text_data=json.dumps({
            'type': 'dash',
            'data': data
        }))


    # async def get_dashboard(self) -> None:
    #     try:
    #         # [("username": pnl), ...]
    #         dash = redis_client1.zrange("dashboard", 0, -1, withscores=True)
    #         await self.send(text_data=json.dumps({
    #             "type": "dash",
    #             "data": {
    #                 "dash": dash
    #             }
    #         }))
    #
    #     except Exception as ex:
    #         await self.send(text_data=json.dumps({
    #             "type": "error",
    #             "message": str(ex)
    #         }))


    async def get_active(self, key):
        try:
            if key is None:
                raise DataError(
                    "Invalid input of type: 'NoneType'. Convert to a bytes, string, int or float first.")

            val = redis_client1.hget("actives", key)
            await self.send(text_data=json.dumps({
                "type": "active",
                "action": "get",
                "value": val if val else None
            }))
        except DataError as ex:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))


    async def user_create(self, username: str) -> None:
        try:
            _ = await self.db_user_create(username)

        except Exception as ex:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))

    async def user_update(self, username: str, wallet: str | None = None, pnl: int | None =None) -> None:
        try:
            obj = await self.db_user_get(username)
            if wallet is not None:
                obj.telegram_wallet = wallet
            if pnl is not None:
                obj.pnl = pnl

            await self.db_make_action("save", obj)

        except Exception as ex:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))

    async def user_get_data(self, username: str) -> None:
        try:
            user = await self.db_user_get(username)
            user_serializer = TelegramUserSerializer(user)

            await self.send(text_data=json.dumps({
                "type": "user",
                "data": {
                    "user":user_serializer.data
                }
            }))

        except Exception as ex:
            logger.debug(ex)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))

    async def user_get_all_data(self, username: str) -> None:
        try:
            user = await self.db_user_get(username)
            trade_pools = await self.db_user_trade_pools(user)
            trade_invs = await self.db_user_trade_invs(user)

            user_serializer = TelegramUserSerializer(user)

            await self.send(text_data=json.dumps({
                "type": "user",
                "data": {
                    "user": user_serializer.data,
                    "trade_pools": trade_pools,
                    "trade_invs": trade_invs
                }
            }))

        except Exception as ex:
            logger.debug(ex)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))

    async def user_destroy(self, username: str) -> None:
        try:
            obj = await self.db_user_get(username)
            await self.db_make_action("delete", obj)

        except Exception as ex:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(ex)
            }))






