from root.config import privileged_users
from root.utils.databases import dbcommands
from aiogram import types


async def add_PUser(user: types.User, user_groups: str):
    """
    Необходимо указать должность, которую занимает пользователь. Например: admins, supports
    :param user: Пользователь.
    :param user_groups: Группа пользователя.
    """
    if user_groups != 'super_admins': return
    users = dbcommands.PUsers()
    privileged_users[user_groups].add((await users.add(user.id))['user_id'])

