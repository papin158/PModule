import enum, typing
from collections import deque

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from root.config import perem_iteration
from ..button_sorter import ButtonSorter


class PermissionNames(int, enum.Enum):
    add_or_delete_group: int
    update_user_group: int
    update_permissions_subgroup: int
    update_faq: int


class SuperUserMenu(CallbackData, prefix="admin_menu"):
    depth: int = 0
    main: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False
    done: bool = False
    ban: bool = False
    add_group: bool = False
    add_user: bool = False
    index_editable_group: typing.Optional[int] = None
    permissions_editable: bool = False
    permission_state: typing.Optional[bool] = None
    permission_name: typing.Optional[int] = None
    subordinate_index: typing.Optional[int] = None
    subordinate_editable: bool = False
    subordinate_state: typing.Optional[bool] = None


class Inline:
    @classmethod
    async def choose_group(cls, depth: int, sub_groups: typing.Iterable,
                           temp_groups: typing.Iterable,
                           menu: typing.Callable = SuperUserMenu,
                           index_editable_group: typing.Optional[int] = None,
                           is_admins: typing.Optional[bool] = None,
                           is_users: typing.Optional[bool] = None,
                           page: int = -1, ban=False,
                           id: int = -1, **kwargs):
        builder = InlineKeyboardBuilder()

        buttons = deque()

        for num, group in enumerate(sub_groups):
            subordinate_state = group in temp_groups
            buttons.append(InlineKeyboardButton(text=f"{'🔴 Убрать' if subordinate_state else '🟢 Добавить'} {group}",
                           callback_data=menu(
                               depth=depth, index_editable_group=index_editable_group, edit=True,
                               subordinate_editable=True, subordinate_index=num, admins=is_admins, users=is_users,
                               subordinate_state=not subordinate_state, id=id, page=page
                           ).pack()))

        ButtonSorter(builder, buttons=buttons).sort()

        builder.row(InlineKeyboardButton(text="Готово", callback_data=menu(
                    depth=depth - 1, edit=True, subordinate_editable=True, done=True,
                    admin=is_admins, users=is_users).pack()))

        builder.row(InlineKeyboardButton(text="Назад", callback_data=menu(
                        depth=depth - 1, edit=True,subordinate_editable=True, id=id,
                        admins=is_admins, users=is_users, page=page).pack()))

        perem_iteration.page = None

        return builder.as_markup()
