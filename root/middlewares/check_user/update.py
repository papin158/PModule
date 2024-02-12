import asyncio

from aiogram import BaseMiddleware, types, Bot
from typing import Dict, Any, Awaitable, Callable

from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat

from root.keyboards.super_users import Inline
from root.middlewares.check_user import close_any_state
from ...config import tech_supports


class CheckUserUpdate(BaseMiddleware):
    """При написании этого класса я уже порядочно просел кукухой и теперь пишу все реализации, которые должны были быть
    вынесены в отдельные функции, в одном классе. Может быть, когда-нибудь я вынесу их в отдельные функции, или даже
    классы, чтобы не засорять один."""
    def __init__(self):
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[Any, Any]], Awaitable[Any]],
            event: types.Update,
            data: Dict[str, Any],
    ) -> Any:
        storage: RedisStorage = data['fsm_storage']
        state: FSMContext = data['state']
        chat: Chat = data['event_chat']
        bot: Bot = data['bot']

        # print(await event.callback_query.message.delete())

        """Реализация Throttling."""
        spam = await storage.redis.get(f'user{data["event_from_user"].id}')
        if spam and event.message and event.message.text and not event.message.text.startswith('/'):
            if int(spam) == 1:
                await storage.redis.set(f'user{data["event_from_user"].id}', value=0, ex=1)
                return await data['bot'].send_message(chat_id=data['event_from_user'].id, text="Вы слишком часто пишете")
            return
        await storage.redis.set(f'user{data["event_from_user"].id}', value=1, ex=1)

        if bytes(f"{data['event_from_user'].id}", 'utf-8') in await data['fsm_storage'].redis.hgetall('banned_users'):
            await data['bot'].send_message(chat_id=data['event_from_user'].id, text="Вы заблокированы.")
            if data.get('raw_state'): await close_any_state(event.message if event.message else event.callback_query, **data)
            await storage.redis.set(f'user{data["event_from_user"].id}', value=0, ex=30)
            return
        """Конец проверки Throttling"""

        """Запись/перезапись пользователя в базу-данных Redis"""
        await data['fsm_storage'].redis.hset(
            "users",
            f"{data['event_from_user'].id}",
            f"""{data['event_from_user'].model_dump_json()}"""
        )
        """Запись завершена"""

        if data.get('raw_state') and event.message and event.message.text and event.message.text.startswith('/'):
            res = await bot.send_message(
                chat_id=chat.id,
                text="Уже существует состояние, удалите его на кнопку", reply_markup=await Inline.close())
            return res
        elif not data.get('raw_state') and data['event_from_user'].id in (tech_supports.tech_supports - tech_supports.tech_supports_in_work) and tech_supports.user_wait:
            res = await bot.send_message(chat_id=chat.id, text="Есть пользователи, которые нуждаются в ответе")
            await handler(event, data)
            return await del_mes(res)

        return await handler(event, data)


async def del_mes(mes):
    await asyncio.sleep(1.76)
    await mes.delete()
