import asyncpg.pool
from aiogram import types, Dispatcher
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from root.utils.data.user_data import file
from typing import Callable, Awaitable, Dict, Any
from root.utils.databases.dbcommands import Context_SQLRequest
users = file[0]


class ActiveQuestion(BaseMiddleware):

    def __init__(self, connector: asyncpg.pool.Pool):
        super().__init__()
        self.connector = connector

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[Any, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any],
    ) -> Any:

        async with self.connector.acquire() as connect:
            data['sqlrequest'] = Context_SQLRequest(connect)
            return await handler(event, data)


        # user = event.from_user

        # try:
        #     if users[f'{user.id}']['receives_response']:
        #         print("Работает")
        #         return
        #     return await handler(event, data)
        # except (ValueError, KeyError) as e:
        #     print(e)
        #     return await handler(event, data)
        # users['']

    # def __init__(self, active: bool = False):
    #     BaseMiddleware.__init__(self)
    #     self.active = active


