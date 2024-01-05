import asyncpg, pprint
from aiogram import BaseMiddleware, types, Bot
from typing import Dict, Any, Awaitable, Callable
from root.utils.databases.redis_db import Users


class CheckUser(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[Any, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any],
    ) -> Any:

        await data['fsm_storage'].redis.hset(
            "users",
            # f"{data['event_from_user'].id}|{data['event_from_user'].username}|{data['event_from_user'].full_name}",
            f"{data['event_from_user'].id}",
            f"""{data['event_from_user'].model_dump_json()}"""
        )


        # pprint.pprint(handler)
        # print('\n\n')
        # pprint.pprint(event.text)
        # print('\n\n')
        # pprint.pprint(data)
        return await handler(event, data)
