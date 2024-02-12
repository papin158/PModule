import typing
from aiogram import BaseMiddleware, types
from aiogram.fsm.storage.redis import RedisStorage


class Throttling(BaseMiddleware):
    def __init__(self, storage: RedisStorage):
        self.storage = storage

    async def __call__(
            self,
            handler: typing.Callable[[types.TelegramObject, typing.Dict[str, typing.Any]], typing.Awaitable[typing.Any]],
            event: types.Message,
            data: typing.Dict[str, typing.Any]
    ):

        spam = await self.storage.redis.get(f'user{data["event_from_user"].id}')
        if spam:
            if int(spam) == 1:
                await self.storage.redis.set(f'user{data["event_from_user"].id}', value=0, ex=3)
                return await event.answer("Вы слишком часто пишете")
            return
        await self.storage.redis.set(f'user{data["event_from_user"].id}', value=1, ex=3)
        return await handler(event, data)
