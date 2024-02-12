import asyncio

import aiogram.fsm.context
from aiogram import types, Bot
from aiogram.types import Message as M, CallbackQuery as CQ
from aiogram.fsm.storage.base import StorageKey
from ...config import tech_supports
from ...utils.execute import always_answer


async def get_new_user_what_wait(com: M | CQ, user_id: int):
    await always_answer(com, text="У вас вопросы, требующие решения")


async def close_any_state(com: types.Message | types.CallbackQuery, **kwargs):
    state: aiogram.fsm.context.FSMContext = kwargs.get('state')
    bot: Bot = kwargs.get('bot')

    if state:
        context = await state.get_data()

        # Если редактируемое и/или удаляемое сообщения существуют - записываем их в соответствующую переменную
        message_for_edit = types.Message.model_validate_json(context['message_for_edit']).as_(
            bot) if context.get('message_for_edit') else None
        del_mes = types.Message.model_validate_json(context['del_mes']).as_(bot) if context.get(
            'del_mes') else None

        # Если пользователь или администратор находятся в переписке, то освобождаем обоих,
        # администратор теперь не занят.
        if await state.get_state() == "ContactSupport:WORK":
            user_contact = context['contact_id']
            user_key = StorageKey(bot_id=bot.id, user_id=user_contact, chat_id=user_contact)
            await state.storage.set_state(user_key, None)
            await state.storage.set_data(user_key, {})
            tech_supports.tech_supports_in_work.discard(user_contact)
            tech_supports.tech_supports_in_work.discard(com.from_user.id)
            await bot.send_message(chat_id=user_contact,
                                   text=f"Другая сторона разорвала связь.")

        # Если редактируемое/удаляемое сообщение существует - удаляем его и очищаем состояние пользователя
        if message_for_edit:
            await state.update_data(message_for_edit=None)
            await message_for_edit.delete()
        if del_mes:
            await state.update_data(del_mes=None)
            await del_mes.delete()
        await state.clear()

        # Тут проверяем, чтобы удаляемое и редактируемое сообщение небыли одной сущностью,
        # далее удаляем сущность
        if (bool(not message_for_edit) or
            bool(message_for_edit and com.message.message_id != message_for_edit.message_id)):
            await com.message.delete()
            if tech_supports.user_wait.get(com.from_user.id): del tech_supports.user_wait[com.from_user.id]
            res = await bot.send_message(chat_id=com.from_user.id, text="Состояние сброшено.")
            await asyncio.sleep(1.76)
            await res.delete()
        return

