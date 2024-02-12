import enum, typing, math
from collections import deque

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from root.config import privileged_users
from root.keyboards import MainMenu, create_order_button
from root.keyboards.FAQ.admin.fsm_state import cancel
from ..super_users import super_users
from root.keyboards import contact_support
from ..button_sorter import ButtonSorter


class GroupEditable(CallbackData, prefix="group_edit"):
    depth: int = 0
    main: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False
    done: bool = False
    ban: bool = False
    index_editable_group: typing.Optional[int] = None
    permissions_editable: bool = False
    permission_state: typing.Optional[bool] = None
    permission_name: typing.Optional[int] = None
    subordinate_index: typing.Optional[int] = None
    subordinate_editable: bool = False
    subordinate_state: typing.Optional[bool] = None


class Inline(super_users.Inline):
    __slots__ = ()

    @classmethod
    async def permissions(cls, depth: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="Создать", callback_data=GroupEditable(depth=depth+1, create=True))
        builder.button(text="Изменить", callback_data=GroupEditable(depth=depth+1, edit=True))
        builder.button(text="Удалить", callback_data=GroupEditable(depth=depth+1, delete=True))
        builder.button(text="Назад", callback_data=super_users.SuperUserMenu(depth=depth))
        builder.adjust(3, 1)
        return builder.as_markup()

    @classmethod
    async def list_groups_for_edit(cls, depth: int, sub_groups: typing.Iterable | typing.Sized,
                                   subordinate_editable: bool,
                                   permissions_editable: bool, edit=True, delete=False):
        builder = InlineKeyboardBuilder()
        if len(sub_groups) > 0:
            for num, group in enumerate(sub_groups):
                builder.button(text=f"{'Изменить' if edit else 'Удалить'} {group}",
                               callback_data=GroupEditable(
                                   depth=depth + 1, index_editable_group=num, edit=edit, delete=delete,
                                   permissions_editable=permissions_editable,
                                   subordinate_editable=subordinate_editable))

        builder.button(text="Назад", callback_data=GroupEditable(
            depth=depth - 1, edit=True, delete=False
        ))

        create_order_button(builder, buttons=sub_groups, custom_buttons=1)

        return builder.as_markup()

    @classmethod
    async def group_permission_edit(cls, depth: int, temp_groups: dict, editable_group: str, index_editable_group: int,
                                    edit: bool, delete: bool, user_id: int):
        builder = InlineKeyboardBuilder()
        num: int = -1

        if 'subordinate_groups' in temp_groups[editable_group]:
            temp_groups[editable_group].pop('subordinate_groups')

        main_buttons = deque()
        super_user = privileged_users[user_id]['super_user']
        for permission_name, permission_state in temp_groups[editable_group].items():
            num += 1
            if not super_user and privileged_users[user_id][permission_name] is False:
                continue

            main_buttons.append(InlineKeyboardButton(
                text=f'{permission_name} ({"А" if permission_state else "Н"})',
                callback_data=GroupEditable(depth=depth,
                                            index_editable_group=index_editable_group, edit=edit,
                                            permission_name=num, permission_state=permission_state,
                                            permissions_editable=True, delete=delete).pack()))

        ButtonSorter(builder, main_buttons).insert_one_position_custom_buttons(
            buttons=(
                InlineKeyboardButton(text="Готово", callback_data=GroupEditable(
                    depth=depth - 1, edit=True, permissions_editable=True, done=True).pack()),
                InlineKeyboardButton(text="Назад", callback_data=GroupEditable(
                    depth=depth - 1, permissions_editable=True, edit=True).pack())
            ),
            position=ButtonSorter.position.after_main_buttons
        ).sort()

        return builder.as_markup()

    @classmethod
    async def group_select_for_edit(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Права группы", callback_data=GroupEditable(
            depth=depth + 1, edit=True, permissions_editable=True))
        builder.button(text="Наследование", callback_data=GroupEditable(
            depth=depth + 1, edit=True, subordinate_editable=True))

        builder.button(text="Назад", callback_data=GroupEditable(depth=depth - 1, edit=True))

        builder.adjust(2)
        return builder.as_markup()

    @classmethod
    async def finish(cls, depth: int, create=False, edit=False, delete=False):
        builder = InlineKeyboardBuilder()
        builder.button(text="Готово", callback_data=GroupEditable(depth=depth-1, create=create,edit=edit, delete=delete, done=True))

        builder.add(await cancel("Отмена"))
        return builder.as_markup()

