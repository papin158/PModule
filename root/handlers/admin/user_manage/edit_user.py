import json
from copy import deepcopy
from io import BytesIO

import aiohttp

from aiogram import types, filters, F, html, Bot
from aiogram.utils.markdown import hide_link
from aiogram.fsm.context import FSMContext

from root.config import privileged_users, JsonUser, update_privileged_users
from root.keyboards.super_users.super_users import UserSuperUserMenu, Inline
from root.utils.databases.redis_db import Users
from root.utils.databases.dbcommands import PUsers, Privileged
from ..telegraph import photo_link_aiograph


async def user_group_selection(call: types.CallbackQuery, callback_data: UserSuperUserMenu, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите группу пользователей", reply_markup=await Inline.what_users(
        depth=callback_data.depth,
    ))


async def user_select(call: types.CallbackQuery, callback_data: UserSuperUserMenu, state: FSMContext, **kwargs):
    context = await state.get_data()
    user_list = await get_user_list(callback_data)
    if callback_data.done:
        await final(context['user']['id'], context['temp_groups'])
    await call.message.edit_text("Выберите пользователя", reply_markup=await Inline.get_users_list(
        depth=callback_data.depth, is_users=callback_data.users, is_admins=callback_data.admins,
        user_list=user_list
    ))
    await state.update_data(user_list=user_list, temp_groups=None)


async def get_user_list(callback_data: UserSuperUserMenu, a_user: types.User = None) -> list[JsonUser]:
    users: list[JsonUser] = await Users().get_user_list(a_user=a_user, to_json=True)
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
        if not pr: del_user = True
        groups = add_groups

    await pusers.add(user_id)
    for group in groups:
        await user_privileges.add(user_id, user_group=group)

    if delete_groups:
        for group in delete_groups:
            await user_privileges.delete(user_id, user_group=group)

    if del_user and not privileged_users[user_id]['super_user']:
        await pusers.delete(user_id)

    await update_privileged_users()


async def get_method(call: types.CallbackQuery, callback_data: UserSuperUserMenu, state: FSMContext, bot: Bot, **kwargs):
    context = await state.get_data()
    user: JsonUser = context['user_list'][callback_data.id]
    a_user: types.User = types.User.model_validate_json(json.dumps(user)).as_(bot)
    user_photos = await a_user.get_profile_photos()
    users_photo = context['users_photo'] if context.get('users_photo') else {f"{callback_data.id}": ''}
    print(f'{users_photo=}')

    if not users_photo.get(f"{callback_data.id}"):
        users_photo[f"{callback_data.id}"] = ''

    link_photo = users_photo[f"{callback_data.id}"]

    if user_photos.total_count > 0 and not link_photo:
        file = await bot.get_file(user_photos.photos[0][-1].file_id)
        new_photo = (await bot.download_file(file.file_path)).read()
        link_photo = await photo_link_aiograph(new_photo)
        users_photo[f"{callback_data.id}"] = link_photo

    sub_groups = context.get('sub_groups') if context.get('sub_groups') else deepcopy(privileged_users[call.from_user.id]['user_subordinate_groups'])
    temp_groups = get_temp_essence(context, user)
    selected_group = sub_groups[callback_data.subordinate_index] if isinstance(callback_data.subordinate_index, int) else None

    if callback_data.subordinate_state and sub_groups and selected_group not in temp_groups:
        temp_groups.append(selected_group)
    elif callback_data.subordinate_state is False and selected_group in temp_groups:
        temp_groups.remove(selected_group)

    link = f'tg://user?id={user["id"]}'
    link = hide_link(link_photo)

    await call.message.edit_text(
        f"""Выберите права для пользователя
        {a_user.mention_html()}""",
        reply_markup=await Inline.choose_group(
            depth=callback_data.depth, is_users=callback_data.users, is_admins=callback_data.admins,
            id=callback_data.id, menu=UserSuperUserMenu, temp_groups=temp_groups,
            sub_groups=sub_groups
    ))
    await state.update_data(temp_groups=temp_groups, sub_groups=sub_groups, user=user, link_photo=link_photo,
                            users_photo=users_photo)


def get_temp_essence(context: dict, user: dict):
    temp_groups = context.get('temp_groups')
    if user and user.get('id') and privileged_users.get(user['id']) and not temp_groups:
        temp_groups = deepcopy(privileged_users[int(user['id'])]['user_groups'])
    elif not temp_groups:
        temp_groups = list()
    return temp_groups