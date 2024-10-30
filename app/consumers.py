import json
import typing
import uuid
import logging
from urllib.parse import parse_qsl

import redis

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import F

from app.models import TelegramUser, TradePool, TradeInvestment
from app.serializers import TelegramUserSerializer, TradePoolSerializer, TradeInvestmentSerializer
from app.utils import verify_telegram_init_data

logger = logging.getLogger("channels")

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class PoolConsumer(AsyncWebsocketConsumer):
    @classmethod
    def update_dashboard(cls, key: str, value: int = 0) -> None:
        redis_client.zadd("dashboard", {key: value})
        redis_client.publish(
            "main.dash_channel",
            json.dumps(redis_client.zrange("dashboard", 0, 3, withscores=True))
        )

    @classmethod
    def load_dashboard(cls) -> list[dict]:
        return json.dumps(redis_client.zrange("dashboard", 0, 3, withscores=True))

    @classmethod
    def delete_user_from_dashboard(cls, key: str) -> None:
        redis_client.zrem("dashboard", key)
        redis_client.publish(
            "main.dash_channel",
            json.dumps(redis_client.zrange("dashboard", 0, 3, withscores=True))
        )

    @classmethod
    def publish_pool(cls, pool: object) -> None:
        redis_client.publish("main.pools_channel", json.dumps({
            "pool": pool
        }))

    @classmethod
    def publish_investment(cls, pool: dict, inv: dict | None = None) -> None:
        redis_client.publish("main.investments_channel", json.dumps({
            "pool": pool,
            "investment": inv
        }))


    @classmethod
    @database_sync_to_async
    def db_user_check(cls, user_id: uuid.UUID) -> bool | typing.NoReturn:
        try:
            return TelegramUser.objects.filter(id=user_id).exists()
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_user_create(cls, data: dict) -> TelegramUser | typing.NoReturn:
        try:
            user_id = uuid.UUID(data["id"])
            username = data.get("username", None)
            photo_url = data.get("photo_url", None)
            return TelegramUser.objects.create(id=user_id, username=username, img=photo_url)
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_user_get(cls, user_id: uuid.UUID = None) -> dict | typing.NoReturn:
        try:
            user = TelegramUser.objects.get(id=user_id)
            ser = TelegramUserSerializer(user)
            return ser.data

        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_user_delete(cls, user_id: uuid.UUID = None) -> None | typing.NoReturn:
        try:
            TelegramUser.objects.filter(id=user_id).delete()
        except Exception as ex:
            logger.exception(str(ex))

    # @classmethod
    # @database_sync_to_async
    # def db_user_trade_pools(cls, user_id: uuid.UUID) -> dict:
    #     try:
    #         trade_pools = TradePool.objects.filter(user_id=user_id)
    #         ser = TradePoolSerializer(trade_pools, many=True)
    #         return ser.data
    #     except Exception as ex:
    #         logger.exception(str(ex))

    # @classmethod
    # @database_sync_to_async
    # def db_user_trade_invs(cls, user_id: uuid.UUID) -> dict:
    #     trade_invs = TradeInvestment.objects.filter(user_id=user_id)
    #     ser = TradeInvestmentSerializer(trade_invs, many=True)
    #     return ser.data

    @classmethod
    @database_sync_to_async
    def db_trade_pool_create(cls, data: dict) -> dict | typing.NoReturn:
        # logger.debug(f"function trade pol create start: {user}, {data}")
        try:
            obj =  TradePool.objects.create(
                user_id=data["user_id"],
                active=data["active"],
                is_long=data["is_long"],
                is_order=data["is_order"],
                order=data["order"],
                final_amount=data["final_amount"],
                stop_loss=data["stop_loss"],
                take_profit=data["take_profit"],
                leverage=data["leverage"],
            )
            # logger.debug(f"after creting pool: {obj}")
            ser = TradePoolSerializer(obj)
            # logger.debug(f"trade pool create funcion: {ser.data}")
            return ser.data
        except Exception as ex:
            logger.debug(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_pool_update(cls, data: dict = None) -> None | typing.NoReturn:
        try:
            TradePool.objects.filter(id=data["id"]).update(curr_value=data["curr_value"], in_amount=data["in_amount"])
            # obj = TradePool.objects.get(id=data["id"])
            # obj.curr_value = data["currValue"]
            # obj.in_amount = data["inAmount"]
            # obj.save()
            #
            # ser = TradePoolSerializer(obj)
            #
            # return ser.data

        except Exception as ex:
            logger.exception(str(ex))

    # @database_sync_to_async
    # def db_trade_pool_get(self, trade_pool_id):
    #     try:
    #         return TradePool.objects.get(id=trade_pool_id)
    #
    #     except Exception as ex:
    #         logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_pool_get_all(cls) -> dict | typing.NoReturn:
        try:
            objs = TradePool.objects.all().order_by('curr_value')
            ser = TradePoolSerializer(objs, many=True)
            return ser.data
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_inv_check(cls, data: dict) -> bool | typing.NoReturn:
        try:
            return TradeInvestment.objects.filter(user_id=data["user_id"], pool_id=data["pool_id"]).exists()
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_inv_create(cls, data: dict) -> None | typing.NoReturn:
        try:
            _ = TradeInvestment.objects.create(
                user_id=data["user_id"],
                pool_id=data["pool_id"],
                input=data["input"],
            )

        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_inv_update(cls, data: dict) -> None | typing.NoReturn:
        # logger.debug(f"db_trade_inv_update, data: {data}")
        try:
            TradeInvestment.objects.filter(user=data["user_id"], trade_idea=data["pool_id"]).update(input=F('input') + data["amount"])
            # ser = TradeInvestmentSerializer(obj)
            #
            # return ser.data
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_inv_get_all(cls) -> dict | typing.NoReturn:
        try:
            objs = TradeInvestment.objects.all()
            ser = TradeInvestmentSerializer(objs, many=True)
            return ser.data
        except Exception as ex:
            logger.exception(str(ex))

    @classmethod
    @database_sync_to_async
    def db_trade_inv_delete(cls, data: dict) -> None | typing.NoReturn:
        try:
            TradeInvestment.objects.filter(user_id=data["user_id"], pool_id=data["pool_id"]).delete()

        except Exception as ex:
            logger.exception(str(ex))


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

        if m_type == "user":
            if action == "auth":
                user_data = await self.verif(params["init_data"])
                user_id = uuid.UUID(user_data["id"])

                if not await self.db_user_check(user_id):
                    await self.db_user_create(user_data)
                    self.update_dashboard(user_id)

                leaderboard = json.loads(self.load_dashboard())
                user = await self.db_user_get(user_id)
                pools = await self.db_trade_pool_get_all()
                invs = await self.db_trade_inv_get_all()

                await self.send(text_data=json.dumps({
                    "type": "auth",
                    "data": {
                        "user": user,
                        "pools": pools,
                        "invs": invs,
                        "dash": leaderboard
                    }
                }))

            else:
                user_id = params["user_id"]
                if action == "update":
                    pnl = params["pnl"]
                    self.update_dashboard(user_id, pnl)
                    await self.db_user_get(user_id)

                elif action == "delete":
                    await self.db_user_delete(user_id)
                    self.delete_user_from_dashboard(user_id)

                elif action == "get":
                    await self.db_user_get(user_id)

        elif m_type == "trade_pool":
            if action == "create":
                pool = await self.db_trade_pool_create(params)
                self.publish_pool(pool)

            elif action == "update":
                investment_data = params.get("investment", None)
                pool_data = params.get("pool", None)

                self.publish_investment(pool_data, investment_data)
                await self.db_trade_pool_update(pool_data)

                if await self.db_trade_inv_check(investment_data):
                    # logger.info("TRADE INVESTMENT UPDATE")
                    await self.db_trade_inv_update(investment_data)
                else:
                    # logger.info("TRADE INVESTMENT CREATE")
                    await self.db_trade_inv_create(investment_data)

        elif m_type == "investment":
            if action == "delete":
                pool_data = params["pool"]
                investment_data = params["investment"]
                self.publish_investment(pool_data)
                await self.db_trade_pool_update(pool_data)
                await self.db_trade_inv_delete(investment_data)



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

        await self.send(text_data=json.dumps({
            'type': 'dash',
            'data': data
        }))

    async def pool(self, event):
        data = event["data"]
        data = json.loads(data)
        # data = json.loads(data["pool"])
        logger.info(f"Pools updatye received: {data}")

        await self.send(text_data=json.dumps({
            "type": "pool",
            "data": data["pool"]
        }))

    # async def update_pool(self, event):
    #     data = json.loads(event["data"])
    #     data = json.loads(data["pool"])
    #
    #     logger.info(f"Update pool: {data}")
    #
    #     await self.send(text_data=json.dumps({
    #         "type": "update_pool",
    #         "data": data["d"]
    #     }))

    async def investment(self, event):
        data = json.loads(event["data"])

        logger.info(f"New investment: {data}")

        await self.send(text_data=json.dumps({
            "type": "investment",
            "data": data
        }))

    # async def user_update(self, username: str, wallet: str | None = None, pnl: int | None =None) -> None:
    #     try:
    #         obj = await self.db_user_get(username)
    #         if wallet is not None:
    #             obj.telegram_wallet = wallet
    #         if pnl is not None:
    #             obj.pnl = pnl
    #
    #         await self.db_make_action("save", obj)
    #
    #     except Exception as ex:
    #         await self.send(text_data=json.dumps({
    #             "type": "error",
    #             "message": str(ex)
    #         }))
    #
    # async def user_get_data(self, username: str) -> None:
    #     try:
    #         user = await self.db_user_get(username)
    #         user_serializer = TelegramUserSerializer(user)
    #
    #         await self.send(text_data=json.dumps({
    #             "type": "user",
    #             "data": {
    #                 "user":user_serializer.data
    #             }
    #         }))
    #
    #     except Exception as ex:
    #         logger.debug(ex)
    #         await self.send(text_data=json.dumps({
    #             "type": "error",
    #             "message": str(ex)
    #         }))

    # async def user_get_all_data(self, user_id: uuid.UUID) -> dict | typing.NoReturn:
    #     try:
    #         user = await self.db_user_get(user_id)
    #         trade_pools = await self.db_user_trade_pools(user.get("id", None))
    #         trade_invs = await self.db_user_trade_invs(user.get("id", None))
    #
    #         return {
    #             "user": user,
    #             "trade_pools": trade_pools,
    #             "trade_invs": trade_invs
    #         }
    #
    #     except Exception as ex:
    #         logger.debug(str(ex))

    # async def user_destroy(self, username: str) -> None:
    #     try:
    #         obj = await self.db_user_get(username)
    #         await self.db_make_action("delete", obj)
    #
    #     except Exception as ex:
    #         await self.send(text_data=json.dumps({
    #             "type": "error",
    #             "message": str(ex)
    #         }))
    #
    #
    #
    #
    # async def trade_pool_create(self, data=None):
    #     try:
    #         user = await self.db_user_get(data.get("username", ""))
    #         active = await self.db_get_active(int(data.get("activeId", "")))
    #
    #         return await self.db_trade_pool_create(user, active, data)
    #
    #     except Exception as ex:
    #         await self.send(text_data=json.dumps({
    #             "type": "error",
    #             "message": str(ex)
    #         }))
    #
    # async def trade_inv_check(self, data):
    #     try:
    #         user = await self.db_user_get(user_id=data.get("userId", ""))
    #         logger.debug(f"trade_inv_check: user, {user}")
    #
    #         trade_pool = await self.db_trade_pool_get(data.get("tradePoolId", ""))
    #         logger.debug(f"trade_inv_check: trade_pool, {trade_pool}")
    #
    #         return await self.db_trade_inv_check(user, trade_pool)
    #
    #     except Exception as ex:
    #         logger.exception(str(ex))
    #
    # async def trade_inv_create(self, data: dict) -> None:
    #     try:
    #         user = await self.db_user_get(user_id=data.get("userId"))
    #         trade_pool = await self.db_trade_pool_get(data.get("tradeIdea", ""))
    #         return await self.db_trade_inv_create(user, trade_pool, data)
    #
    #     except Exception as ex:
    #         logger.exception(str(ex))
    #
    #
    # async def trade_inv_update(self, data):
    #     try:
    #         user = await self.db_user_get(user_id=data.get("userId"))
    #         trade_pool = await self.db_trade_pool_get(data.get("tradeIdea", ""))
    #
    #         return await self.db_trade_inv_update(user, trade_pool, data)
    #
    #     except Exception as ex:
    #         logger.exception(str(ex))
    #
    # async def trade_inv_delete(self, data):
    #     try:
    #         user = await self.db_user_get(user_id=data.get("userId", None))
    #         trade_pool = await self.db_trade_pool_get(data.get("tradeIdea", None))
    #         await self.db_trade_inv_delete(user, trade_pool)
    #
    #     except Exception as ex:
    #         logger.exception(str(ex))