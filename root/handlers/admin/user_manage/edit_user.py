import json
import math
import typing
from copy import deepcopy

from aiogram import types, filters, F, html, Bot
from aiogram.utils.markdown import hide_link
from aiogram.fsm.context import FSMContext

from root.config import privileged_users, JsonUser, update_privileged_users, perem_iteration
from root.keyboards.super_users import UserEditable, Inline
from root.utils.databases.redis_db import Users, BannedUsers
from root.utils.databases.dbcommands import PUsers, Privileged
from ..telegraph import photo_link_aiograph
import root.handlers.admin.user_manage.ban_user


async def user_group_selection(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите группу пользователей", reply_markup=await Inline.what_users(
        depth=callback_data.depth,
    ))
    perem_iteration.page = None
    await state.set_state(None)


async def user_select(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    context = await state.get_data()
    # await state.clear()
    user_list = await get_user_list(callback_data)
    if callback_data.done:
        await final(context['user']['id'], context['temp_groups'])
    if isinstance(perem_iteration.page, int) and perem_iteration.page == callback_data.page:
        return await call.answer(f"Вы на {callback_data.page + 1} странице")
    await call.message.edit_text("Выберите пользователя", reply_markup=await Inline.get_users_list(
        depth=callback_data.depth, is_users=callback_data.users, is_admins=callback_data.admins,
        user_list=user_list, page=callback_data.page, step=1,  ban=context.get('ban')
    ))
    perem_iteration.page = callback_data.page
    await state.update_data(user_list=user_list, temp_groups=None, page=callback_data.page)
    await state.set_state(None)


async def get_user_list(
        callback_data: UserEditable, a_user: types.User = None,
        method: typing.Literal["to_json"] | typing.Literal["raw"] = 'to_json') -> list[JsonUser]:
    method = {method: True}
    users: list[JsonUser] = await Users().get_user_list(a_user=a_user, **method)
    banned_users = await BannedUsers().get(**method)
    new_users: list[JsonUser] = []
    for user in users:
        if user not in banned_users: new_users.append(user)

    users = new_users

    if callback_data.users:
        return users

    urs: list[JsonUser] = []
    for user in users:
        for puser in privileged_users.keys():
            if user['id'] == puser:
                urs.append(user)
    return urs


async def final(user_id, groups, **kwargs):
    pusers = PUsers()
    user_privileges = Privileged()
    delete_groups = None
    del_user = None

    if privileged_users.get(user_id):
        pr = set(privileged_users[user_id]['user_groups'])
        grp = set(groups)
        add_groups = grp - pr
        delete_groups = pr - grp
        groups = add_groups
        if len(pr - delete_groups) == 0:
            del_user = True

    await pusers.add(user_id)
    for group in groups:
        await user_privileges.add(user_id, user_group=group)

    if delete_groups:
        for group in delete_groups:
            await user_privileges.delete(user_id, user_group=group)

    if del_user and not privileged_users[user_id]['super_user']:
        await pusers.delete(user_id)

    await update_privileged_users()


async def get_method(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, bot: Bot, **kwargs):
    context = await state.get_data()
    user: JsonUser = context['user_list'][callback_data.id]
    a_user: types.User = types.User.model_validate_json(json.dumps(user)).as_(bot)
    if callback_data.ban:
        if callback_data.ban_list:
            return await root.handlers.admin.user_manage.ban_user.unban(call, callback_data, state)
        return await root.handlers.admin.user_manage.ban_user.choose_user(call, callback_data, state)
    # user_photos = await a_user.get_profile_photos()
    # users_photo = context['users_photo'] if context.get('users_photo') else {f"{callback_data.id}": ''}
    #
    # if not users_photo.get(f"{callback_data.id}"):
    #     users_photo[f"{callback_data.id}"] = ''
    #
    # link_photo = users_photo[f"{callback_data.id}"]
    #
    # if user_photos.total_count > 0 and not link_photo:
    #     file = await bot.get_file(user_photos.photos[0][-1].file_id)
    #     new_photo = (await bot.download_file(file.file_path)).read()
    #     link_photo = await photo_link_aiograph(new_photo)
    #     users_photo[f"{callback_data.id}"] = link_photo

    sub_groups = context.get('sub_groups') if context.get('sub_groups') else deepcopy(privileged_users[call.from_user.id]['user_subordinate_groups'])
    temp_groups = get_temp_essence(context, user)
    selected_group = sub_groups[callback_data.subordinate_index] if isinstance(callback_data.subordinate_index, int) else None

    if callback_data.subordinate_state and sub_groups and selected_group not in temp_groups:
        temp_groups.append(selected_group)
    elif callback_data.subordinate_state is False and selected_group in temp_groups:
        temp_groups.remove(selected_group)

    # link = f'tg://user?id={user["id"]}'
    # link = hide_link(link_photo)
    username_link = f'http://t.me/{a_user.username}'

    await call.message.edit_text(
        f"""Выберите права для пользователя
        {hide_link(username_link)}""",
        reply_markup=await Inline.choose_group(
            depth=callback_data.depth, is_users=callback_data.users, is_admins=callback_data.admins,
            id=callback_data.id, menu=UserEditable, temp_groups=temp_groups,
            sub_groups=sub_groups, page=callback_data.page, ban=context.get('ban')
    ))
    await state.update_data(temp_groups=temp_groups, sub_groups=sub_groups, user=user, link_photo='link_photo',
                            users_photo='users_photo')


def get_temp_essence(context: dict, user: dict):
    temp_groups = context.get('temp_groups')
    if user and user.get('id') and privileged_users.get(user['id']) and not temp_groups:
        temp_groups = deepcopy(privileged_users[int(user['id'])]['user_groups'])
    elif not temp_groups:
        temp_groups = list()
    return temp_groups
