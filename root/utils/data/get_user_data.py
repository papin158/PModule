from aiogram import types
from root.utils.logic.UserContext import CurrentUser
from root.utils.data.user_data import file

users = file[0]


async def get_user(user: types.User):
    """
    Если у пользователя уже есть свой контекст в боте, то возвращаем ему его, если нет создаём и записываем в память.
    :param user: Получаем данные пользователя.
    :return: Возвращаем пользователя, который имеет свой контекст.
    """
    if f"{user.id}" in users:
        current_user: CurrentUser = users[f'{user.id}'].loc['context']
    else:
        current_user: CurrentUser = CurrentUser(user=user)
        users[f"{user.id}"] = [user, current_user, False]
        users.index = ['user', 'context', 'receives_response']

    return current_user
