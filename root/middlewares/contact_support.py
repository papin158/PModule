from typing import Any, Awaitable, Callable, Dict, TypeVar

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject, CallbackQuery, Update
from ..config import privileged_users, tech_supports
from ..keyboards.contact_support import Inline
from ..utils.fsm.contact_support import ContactSupport


class Contact(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data.get('state')
        if state:
            user_state = await state.get_state()
            context = await state.get_data()
            if user_state == "ContactSupport:WORK" and event.message:
                return await self.bot.copy_message(
                    context['contact_id'], event.message.from_user.id, event.message.message_id,
                    reply_markup=await Inline.cancel(text="Закончить диалог")
                )

        await handler(event, data)

    async def user_state_wait_check(self, state: FSMContext):
        user_no_wait = set()
        for user_id in tech_supports.user_wait:
            user_key = StorageKey(bot_id=self.bot.id, user_id=user_id, chat_id=user_id)
            user_current_state = await state.storage.get_state(user_key)

    def if_user_work(self, current_state) -> str:
        if current_state != "ContactSupport:WAIT":
            if current_state != "ContactSupport:WORK":
                return "Пользователь прекратил ожидание"
            else:
                return "Другой администратор принял запрос"
        return ""

    async def send_supports(self, user_id: int, text: str):
        for support in tech_supports.tech_supports:
            if user_id == support: continue
            await self.bot.edit_message_text(text, support, 1111)
