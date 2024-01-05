import asyncio
import typing

import aiogram.types
import g4f, enum, json, math, numpy as np
from aiogram import Router, F, filters, html
from aiogram.types import Message, User, CallbackQuery
from root.keyboards.AI.models import Inline, GPTCallback
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest
from root.utils.logic.UserContext import CurrentUser
from root.utils.data.get_user_data import file, get_user
from root.middlewares.request_delay import ActiveQuestion
from text import ReservWords

g4f.debug.logging = True  # enable logging
g4f.check_version = True  # Disable automatic version checking


async def get_message(message: Message, command: filters.CommandObject = None):
    """
     Проверят, отправлено ли сообщение в Личные Сообщения боту, или через команду {command} в группе.
     Если команда отправлена в личные сообщения, игнорировать.
    :param message: Само сообщение, которое было поймано хендлером.
    :param command: Команда, которая может присутствовать.
    :return:
    """

    current_user: CurrentUser = await get_user(message.from_user)  # Получаем контекст текущего пользователя
    if not users[f"{message.from_user.id}"]['receives_response']:
        users[f"{message.from_user.id}"]['receives_response'] = True
        if (message.chat.type in {"supergroup", "group"}) and command:                          # Проверяем, если запрос написан в группе, он должен быть с командой
            await current_user.user_message_from_any_group(message=message, command=command)    # Генерируем ответ в группу
        else: await current_user.user_message(message)                                          # Если запрос был в личных сообщениях - генерируем ответ туда
    elif not command:
        m = await message.answer("У вас уже есть активный вопрос, дождитесь ответа")
        await asyncio.sleep(3)
        await message.delete()
        await m.delete()
    else:
        await message.reply("У вас уже есть активный вопрос, дождитесь ответа")


async def set_gpt_provider(call: CallbackQuery, version, provider, id, depth, **kwargs):
    """
    :param call: Получаем сам коллбек.
    :param callback_data: Получаем данные, которые находятся в нажатой кнопке, в данном случае там находятся параметры
    {GPT4Callback.model} и {GPT4Callback.id}.
    :return: Функция ничего не возвращает, только отвечает на запрос по нажатию кнопки.
    """
    users[f'{call.from_user.id}']['context'].provider = (await Inline.choice_gpt(version))[id-1]                        # Передаём в функцию пользователя другого поставщика GPT
    await call.message.edit_text(text=f"Модель изменена на {provider}")                                                 # Уведомляем пользователя о смене поставщика услуги
    await call.answer()                                                                                                 # Убираем "часики" с кнопки


async def choice_gpt_provider(call: CallbackQuery, version, depth, **kwargs):
    """
    Выдаём пользователю перечень кнопок, которые отвечают за выбор версии GPT.
    :param call: Получение коллбека.
    :param version: Присваиваем версию.
    :param depth: Глубина кнопки.
    :return: Ничего не возвращаем.
    """
    if version == 3: gpt = "gpt-3.5-turbo"
    elif version == 4: gpt = "gpt-4"
    users[f'{call.from_user.id}']['context'].model = gpt                                              # Передаём версию GPT
    await call.message.edit_text(f"Выберите версию", reply_markup=await Inline.kb_gpt_provider(version, depth=depth))


async def gpt_choice(call: CallbackQuery, depth, **kwargs):
    await call.message.edit_text("Выберите версию GPT", reply_markup=(await Inline.kb_choice_gpt(depth=depth)))


async def settings(message: Message | CallbackQuery, depth: int = 0, **kwargs):
    await get_user(message.from_user)
    if isinstance(message, CallbackQuery):
        call = message
        with suppress(TelegramBadRequest):
            await call.message.edit_text("Настройте своего помощника", reply_markup=await Inline.kb_settings(depth=depth))
    else:
        await message.answer("Настройте своего помощника", reply_markup=await Inline.kb_settings(depth=depth))


async def settings_navigate(call: CallbackQuery, callback_data: GPTCallback):
    depth = {
        0: settings,
        1: gpt_choice,
        2: choice_gpt_provider,
        3: set_gpt_provider,
    }

    current_depth_func = depth[callback_data.current_depth]

    """____________________________________________________________________________________________
    ______________________________ДОРАБОТАТЬ_______________________________________________________
    __НЕ СБРАСЫВАЕТ КОНТЕКСТ, ЕСЛИ У ПОЛЬЗОВАТЕЛЯ ЕГО НЕТ, ВЫЗЫВАЕТСЯ ОШИБКА_______________________
    _______________________________________________________________________________________________
    """

    if callback_data.clear_context: # Если у пользователя есть контекст удалить
        return await clear_user_context(call=call)

    # _____________________________________________________________________________________________

    await current_depth_func(
        call,
        version=callback_data.version,
        provider=callback_data.provider,
        id=callback_data.id,
        depth=callback_data.current_depth,
    )


async def clear_user_context(call: CallbackQuery):   #Нужно для очистки контекста
    await users[f'{call.from_user.id}']['context'].clear()
    await call.message.edit_text("Контекст удалён", reply_markup=None)


users = file[0]

router = Router()


"""---------------------------------------------------------------------------------------------------------------------
------------------------Поиск пользователей по базе данных с помощью имени пользователя-----------------------------
-----------------------------ID-пользователя или с помощью nickname пользователя------------------------------------
---------------------------------------------------------------------------------------------------------------------
"""
async def get_users(message: Message, bot, fsm_storage, *text_args, **kwargs):
    # import re
    from root.config import pool
    if message.text.startswith("get_user "):
        text_args = message.text.split()
        text_args = ' '.join(text_args[1:]) if len(text_args) > 2 else text_args[1]

        find = []
        text_find_user = "\n"
        users = await pool.Redis.hgetall('users')
        for user in users:
            user_args = user.split('|')
            for arg in user_args:
                if text_args == arg: find.append(User.model_validate_json(users[user]).as_(bot))

        for user in find:
            text_find_user += f"{user.mention_html()}\n"
        await message.answer(f"Вот что я нашёл: {text_find_user}")

    else: await message.answer("text")


async def get_users2(message: Message):
    from root.config import pool
    if message.text.startswith("get_user "):
        text_args = message.text.split()
        text_args = ' '.join(text_args[1:]) if len(text_args) > 2 else text_args[1]

        find: list[User] = []
        text_find_user = "\n"
        users = await pool.Redis.hgetall('users')
        for user in users:
            if user.isdigit():
                user = User.model_validate_json(users[user])
                user_id: typing.Optional[int] = None
                if text_args.isdigit(): user_id = int(text_args)
                if user.id == user_id or user.username == text_args\
                        or user.first_name == text_args or user.last_name == text_args\
                        or user.full_name == text_args:
                    find.append(user)

        for user in find:
            text_find_user += f"{user.mention_html()}\n"
        await message.answer(f"Вот что я нашёл: {text_find_user}")

    else:
        await message.answer("text")

# ----------------------------------------------------------------------------------------------------------------------


async def reserved_words(message: Message, *args, **kwargs):
    if message.text.lower() in ReservWords.динах:
        return await message.answer("Катись в пизду, маленький пидорас, БАН НАХУЙ")
    elif message.text.lower() == ReservWords.ассаламалейкум:
        return await message.answer("أنا لا أفهم لغة العاهرات والإرهابيين! اذهبوا إلى الشيطان أيها المنحطون! غير صحيح!")

    # print(message.text.lower(), '  ', ReservWords.ассаламалейкум)

    await get_users2(message=message)


# router.message.middleware(ActiveQuestion())
router.callback_query.register(settings_navigate, GPTCallback.filter())
router.message.register(settings, filters.Command("settings"))
router.message.register(get_message, filters.Command("generic"))
router.message.register(reserved_words)
router.message.register(get_users)
