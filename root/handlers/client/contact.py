import asyncio
from collections import deque

from aiogram import types, Router, F, filters, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from ...config import tech_supports, UserWait
from ...keyboards.contact_support import Inline, SupportContact
from ...utils.execute import always_answer, execute
from ...utils.fsm.contact_support import ContactSupport

router = Router()


async def contact(call: types.CallbackQuery, callback_data: SupportContact, state: FSMContext, bot: Bot, **kwargs):
    mes = await call.message.edit_text("Вы отправили запрос на связь с тех. поддержкой, ожидайте ответа, "
                                       "или можете не ждать", reply_markup=await Inline.cancel())
    response_messages = deque()
    tech_supports_free = tech_supports.tech_supports - tech_supports.tech_supports_in_work
    if not tech_supports_free:
        return await call.message.edit_text("Все администраторы заняты, напишите позднее")
    for support in tech_supports_free:
        if call.from_user.id == support: continue
        message = await bot.send_message(
            support, text=f"Был отправлен запрос на связь с пользователем: {call.from_user.mention_html()}",
            reply_markup=await Inline.send_to_tech(user_id=call.from_user.id)
        )
        response_messages.append((support, message.message_id))

    tech_supports.user_wait = UserWait(user_id=call.from_user.id,
                                       user_message_id=mes.message_id,
                                       supports_args=response_messages)

    await state.set_state(ContactSupport.WAIT)


async def support_accept_contact(call: types.CallbackQuery, callback_data: SupportContact, state: FSMContext, bot: Bot):
    user_key = StorageKey(bot_id=bot.id, user_id=callback_data.user_id, chat_id=callback_data.user_id)
    user_current_state = await state.storage.get_state(user_key)

    if user_current_state != "ContactSupport:WAIT":
        await call.message.edit_text(text="Пользователь отменил вызов")
        await call.answer(text="Пользователь отменил вызов")
        return

    mes_no_edit = await call.message.edit_text("Вы вышли на связь", reply_markup=await Inline.cancel(text="Закончить"))

    await another_admin_call(callback_data=callback_data, bot=bot, support_agent_took_call=call.from_user.id)

    await bot.edit_message_text(
        chat_id=callback_data.user_id,
        message_id=tech_supports.user_wait[callback_data.user_id].user_message_id,
        text="Администратор на связи",
        reply_markup=await Inline.cancel(text="Закончить")
    )

    tech_supports.tech_supports_in_work.add(call.from_user.id)
    tech_supports.user_wait.pop(callback_data.user_id)

    await state.update_data(contact_id=callback_data.user_id)
    await state.storage.update_data(user_key, {"contact_id": call.from_user.id})
    await state.set_state(ContactSupport.WORK)
    await state.storage.set_state(user_key, ContactSupport.WORK)


async def alo(message: types.Message, command: filters.CommandObject):
    await message.answer(text='ALO', reply_markup=await Inline.contact())


async def cto(message: types.Message, callback_data: SupportContact = None, command: filters.CommandObject = None):
    if callback_data and (0 > callback_data.coord or callback_data.coord >= len(tech_supports.user_wait)):
        return await message.answer(text="Там никого нет")

    await execute(message, text='cto', reply_markup=await Inline.get_user_list(callback_data.coord if callback_data else 0, sep=1))


async def another_admin_call(callback_data: SupportContact, bot: Bot, support_agent_took_call: int):
    messages: deque[types.Message] = deque()
    for support_id, message_id in tech_supports.user_wait[callback_data.user_id].supports_args:
        if support_id == support_agent_took_call: continue
        try:
            messages.append(await bot.edit_message_text(
                text="Другой администратор принял запрос", chat_id=support_id, message_id=message_id
            ))
        except TelegramBadRequest:
            pass
    await asyncio.sleep(1.76)

    for message in messages:
        await message.delete()

    del messages


# router.message.register(alo, filters.Command("alo"))
# router.message.register(cto, filters.Command("cto"))
router.callback_query.register(cto, SupportContact.filter(F.coord.as_(int)))
router.callback_query.register(contact, SupportContact.filter(F.as_user.is_(True)))
router.callback_query.register(support_accept_contact, SupportContact.filter(F.as_user.is_(False)))
