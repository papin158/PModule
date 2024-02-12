import enum, typing, math
from collections import deque

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from .super_users import SuperUserMenu
from ..button_sorter import ButtonSorter


class UserEditable(CallbackData, prefix="user_editable"):
    depth: int = 0
    id: int = -1
    ban: bool = False
    ban_list: bool = False
    create: bool = False
    delete: bool = False
    done: bool = False
    users: bool = False
    admins: bool = False
    page: int = 0
    subordinate_state: typing.Optional[bool] = None
    subordinate_index: typing.Optional[int] = None


class Inline:
    @classmethod
    async def work_with_users(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Список", callback_data=UserEditable(depth=depth + 1))
        builder.button(text="Добавить",
                       callback_data=UserEditable(depth=depth + 2, create=True, ban=False))
        builder.button(text="Забанить",
                       callback_data=UserEditable(depth=depth + 2, users=True, ban=True))
        builder.button(text="Назад", callback_data=SuperUserMenu(
            depth=depth - 1, ban=False, ban_list=False, create=False, users=False, admins=False
        ))
        builder.adjust(2, 1)
        return builder.as_markup()

    @classmethod
    async def what_users(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Пользователи",
                       callback_data=UserEditable(depth=depth + 1, users=True, ban=False))
        builder.button(text="Сотрудники",
                       callback_data=UserEditable(depth=depth + 1, admins=True, ban=False))
        builder.button(text="Заблокированные",
                       callback_data=UserEditable(depth=depth + 1, ban_list=True, ban=True))
        builder.button(text="Назад", callback_data=UserEditable(
            depth=depth - 1, ban=False, ban_list=False, users=False, admins=False
        ))
        builder.adjust(2, 1)
        return builder.as_markup()

    @classmethod
    async def get_users_list(cls, depth: int, user_list: typing.Collection[types.User | dict], is_users: bool = False,
                             is_admins: bool = False, page: int = 0, step: int = 10, ban=False, ban_list=False,
                             as_user=False, menu=UserEditable,
                             back_menu=UserEditable):
        builder = InlineKeyboardBuilder()
        ban = bool(ban)
        is_json = False

        if user_list:
            temp = iter(user_list)
            if isinstance(next(temp), dict): is_json = True
            del temp

            x = page * step
            y = x + step
            pages = math.ceil(len(user_list) / step)

            buttons = deque()

            for num, user in enumerate(user_list[x:y]):
                user_id = None
                if isinstance(user, typing.Tuple):
                    user_id, user = user
                buttons.append(InlineKeyboardButton(
                    text=user.full_name if not is_json else f"{user['first_name']} {user['last_name']}",
                    callback_data=menu(
                        depth=depth + 1, id=num + x, users=is_users, admins=is_admins, page=page, ban=ban,
                        ban_list=ban_list,
                        as_user=as_user, user_id=user['id'] if is_json else user_id).pack()
                ))

            sorted_buttons = ButtonSorter(builder, buttons)

            if page > 0:
                sorted_buttons.grouping_buttons_by_position(
                    InlineKeyboardButton(text=f"Назад {page}/{pages}", callback_data=menu(
                        depth=depth, users=is_users, admins=is_admins, page=page - 1, ban=ban,
                        ban_list=ban_list).pack())
                )

            sorted_buttons.grouping_buttons_by_position(
                InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data=menu(
                        depth=depth, users=is_users, admins=is_admins, page=page, ban=ban,
                        ban_list=ban_list).pack()))

            if page + 1 < pages:
                sorted_buttons.grouping_buttons_by_position(
                    InlineKeyboardButton(text=f"Далее {page + 2}/{pages}", callback_data=menu(
                        depth=depth, users=is_users, admins=is_admins, page=page + 1, ban=ban,
                        ban_list=ban_list).pack()))

            sorted_buttons.grouping(sorted_buttons.position.after_main_buttons).sort()

        builder.row(InlineKeyboardButton(text="К выбору", callback_data=back_menu(
            depth=depth - 2 if ban and not ban_list else depth - 1, users=is_users, admins=is_admins, ban=ban,
            ban_list=ban_list).pack()))
        return builder.as_markup()
