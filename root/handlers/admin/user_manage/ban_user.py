import json

import root.handlers.admin.user_manage.edit_user
from aiogram import types, F
from aiogram.fsm.context import FSMContext

from root.keyboards.FAQ.admin.fsm_state import fsm_start
from root.keyboards.super_users import UserEditable, Inline
from root.utils.fsm.admin_menu import AddNewGroup
from root.utils.databases.redis_db import BannedUsers
from root.config import privileged_users, perem_iteration


async def ban(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    kwargs.update(callback_data=callback_data, state=state)
    callback_data.ban = True
    callback_data.users = True
    if callback_data.ban_list and not callback_data.done:
        return await ban_list(call, **kwargs)

    users_banned = await BannedUsers().get(to_json=True)
    user_list = await root.handlers.admin.user_manage.edit_user.get_user_list(callback_data)
    true_user_list = []

    for user in user_list:
        if not privileged_users.get(user['id']) and user not in users_banned:
            true_user_list.append(user)

    if callback_data.done:
        return await finish(
            call, callback_data=callback_data, true_user_list=true_user_list, banned_list=users_banned, state=state
        )
    await fsm_start(
        message=call,
        text="Введите пользователя или выберите его из списка", fsm_state=AddNewGroup.FIND_USER,
        markup=Inline.get_users_list, p_f_c_b={
            "depth": callback_data.depth, "is_users": True, "is_admins":  callback_data.admins,
            "user_list": true_user_list, "page": callback_data.page, "step": 10, "ban": callback_data.ban
        }, without_exit=True, is_i=True, **kwargs)
    await state.update_data(ban=callback_data.ban, user_list=true_user_list)


async def choose_user(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    await call.message.edit_text(
        "Этот пользователь будет заблокирован",
        reply_markup=await Inline.confirm(
            depth=callback_data.depth,
            create=callback_data.create,
            menu=UserEditable,
            delete=callback_data.delete,
            ban=callback_data.ban,
            id=callback_data.id
        ))
    perem_iteration.i = None


async def finish(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    kwargs.update(callback_data=callback_data, state=state)
    if callback_data.ban and not callback_data.ban_list:
        return await banned(call, **kwargs)
    else:
        return await unbanned(call, **kwargs)


async def banned(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, true_user_list: list, **kwargs):
    user_banned = BannedUsers()
    await user_banned.add(true_user_list[callback_data.id])
    await state.clear()
    return await call.message.edit_text(
        "Пользователь заблокирован"
    )


async def unbanned(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, banned_list: list, **kwargs):
    banned_user = BannedUsers()
    await banned_user.delete(banned_list[callback_data.id])
    await state.clear()
    return await call.message.edit_text(
        "Пользователь разблокирован"
    )


async def ban_list(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    banned_users = BannedUsers()
    user_bans = await banned_users.get(to_json=True)
    await call.message.edit_text(
        "Список всех заблокированных",
        reply_markup=await Inline.get_users_list(
            depth=callback_data.depth, is_users=True, is_admins=callback_data.admins,
            user_list=user_bans, page=callback_data.page, step=10, ban=callback_data.ban, ban_list=True
        ),
    )
    await state.update_data(user_list=user_bans)


async def unban(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    await call.message.edit_text(
        "Пользователь будет разблокирован",
        reply_markup=await Inline.confirm(
            depth=callback_data.depth, create=callback_data.create, menu=UserEditable, ban=callback_data.ban,
            ban_list=callback_data.ban_list, id=callback_data.id, delete=callback_data.delete
        )
    )
