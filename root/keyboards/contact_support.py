from collections import deque
from typing import Optional, NamedTuple

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from . import all_keyboards_for_main_manu, Iteration_CallbackData
from .FAQ.admin.fsm_state import cancel
from .super_users import super_users
from .button_sorter import ButtonSorter
from ..config import tech_supports
from ..utils.databases.redis_db import Users


class Coord(NamedTuple):
    START: int = 0
    END: int = 10


class SupportContact(CallbackData, prefix="support_call"):
    user_id: Optional[int] = None
    as_user: Optional[bool] = None
    coord: Optional[int] = None


class Inline:
    __slots__ = ()

    @staticmethod
    async def send_to_tech(user_id: Optional[int] = None):
        builder = InlineKeyboardBuilder()
        builder.button(text="Ответить", callback_data=SupportContact(as_user=False, user_id=user_id))
        builder.row(await cancel("Назад"))
        return builder.as_markup()

    @staticmethod
    async def contact():
        builder = InlineKeyboardBuilder()
        builder.button(text="Обратиться в ТП", callback_data=SupportContact(as_user=True, user_id=None))
        return builder.as_markup()

    @classmethod
    async def cancel(cls, *args, **kwargs):
        text = kwargs['text'] if kwargs.get('text') else "Закрыть"
        builder = InlineKeyboardBuilder()
        button = await cancel(text)
        builder.row(button)
        return builder.as_markup()

    @classmethod
    async def get_user_list(cls, coord: int = 0, sep=10):
        if not coord: coord = 0
        builder = InlineKeyboardBuilder()
        next_coord = coord+sep
        buttons = deque()
        for user_id in list(tech_supports.user_wait.keys())[coord:next_coord]:
            user = await Users().get_user_for_id(user_id)
            buttons.append(InlineKeyboardButton(
                text=user.full_name, callback_data=SupportContact(
                    user_id=user_id, as_user=False
                ).pack()))

        custom_buttons = (
            InlineKeyboardButton(text="Назад", callback_data=SupportContact(coord=coord-sep).pack()),
            InlineKeyboardButton(text="Далее", callback_data=SupportContact(coord=next_coord).pack())
             )

        ButtonSorter(builder, buttons, rows=2).insert_one_position_custom_buttons(
            buttons=custom_buttons, position=ButtonSorter.position.after_main_buttons
        ).sort()

        builder.row(InlineKeyboardButton(text="В меню", callback_data=super_users.SuperUserMenu(depth=0).pack()))
        return builder.as_markup()


all_keyboards_for_main_manu.append(
    Iteration_CallbackData(description="Обратиться в ТП", callback=SupportContact(as_user=True, user_id=None))
)