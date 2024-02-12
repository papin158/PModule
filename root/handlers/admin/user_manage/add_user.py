import json
import typing

from aiogram import types, filters, Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext

from root.config import privileged_users, perem_iteration
from root.keyboards.FAQ.admin.fsm_state import fsm_start
from root.keyboards.super_users import UserEditable, Inline
from root.utils.fsm.admin_menu import AddNewGroup


async def add_user(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, bot: Bot, **kwargs):
    await fsm_start(
        message=call, state=state, depth=callback_data.depth,
        text="Введите данные пользователя, чтобы добавить оного",
        fsm_state=AddNewGroup.FIND_USER, markup=None,
        without_exit=True)


async def find_user(message: types.Message, state: FSMContext, bot, fsm_storage: RedisStorage, **kwargs):
    context = await state.get_data()
    message_for_edit = types.Message.model_validate_json(context['message_for_edit']).as_(bot)
    text_args = message.text.split()
    text_args = ' '.join(text_args[:]) if len(text_args) > 2 else text_args[0]
    perem_iteration.i = None

    find: list[dict] = []
    users = await fsm_storage.redis.hgetall('users')
    sorted_users = list(sorted(set(await fsm_storage.redis.hgetall('users')) - set(await fsm_storage.redis.hgetall('banned_users'))))
    for user in sorted_users:
        if user.isdigit():
            user = json.loads(users[user])
            user_id: typing.Optional[int] = None
            if text_args.isdigit(): user_id = int(text_args)
            if user['id'] == user_id or user['username'] == text_args\
                    or user['first_name'] == text_args or user['last_name'] == text_args\
                    or f"{user['first_name']} {user['last_name']}" == text_args:
                if context.get('ban') and privileged_users.get(user['id']): continue
                find.append(user)
    del sorted_users
    await message.delete()
    await state.update_data(user_list=find)
    if find:
        await message_for_edit.edit_text(f"Вот кого я нашёл: ", reply_markup=await Inline.get_users_list(
            depth=context['depth'], user_list=find, is_users=True, ban=bool(context.get('ban'))
        ))
    else:
        await message_for_edit.edit_text(
            "Никого не найдено, можете попробовать написать ещё что-то, или нажать \"отмена\"",
            reply_markup=await Inline.close()
        )
