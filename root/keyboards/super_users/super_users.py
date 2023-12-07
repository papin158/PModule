from aiogram import types, filters, F, html
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from root.config import privileged_users, super_admins
from root.keyboards import all_keyboards_for_main_manu, Iteration_CallbackData, MainMenu
import typing


class SuperUserMenu(CallbackData, prefix="admin_menu"):
    is_admin: bool = True


class Inline:
    @classmethod
    async def SUmain(cls, user: types.User, depth: int, user_groups: typing.List[str], translate_groups: typing.List[str]):
        if not translate_groups: translate_groups = user_groups
        builder = InlineKeyboardBuilder()


        [builder.button(text=f"Добавить {group}а", callback_data='') for n, group in enumerate(user_groups)]

        builder.button(text="Назад", callback_data=MainMenu(main=True))
        builder.adjust(1)
        return builder.as_markup()


all_keyboards_for_main_manu.append(
    Iteration_CallbackData(description="Панель администратора", callback=SuperUserMenu(is_admin=True))
)
