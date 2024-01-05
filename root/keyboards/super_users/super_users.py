import enum
from aiogram import types, filters, F, html
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from root.config import privileged_users, groups
from root.keyboards import all_keyboards_for_main_manu, Iteration_CallbackData, MainMenu, exe, create_order_button
from root.keyboards.FAQ.admin.fsm_state import cancel
import typing, itertools, math, numpy as np


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
    add_group: bool = False
    add_user: bool = False
    index_editable_group: typing.Optional[int] = None
    editable_user_id: int = -1
    permissions_editable: bool = False
    permission_state: typing.Optional[bool] = None
    permission_name: typing.Optional[int] = None
    subordinate_index: typing.Optional[int] = None
    subordinate_editable: bool = False
    subordinate_state: typing.Optional[bool] = None


class UserSuperUserMenu(CallbackData, prefix="user_admin_menu"):
    depth: int = 0
    id: int = -1
    ban: bool = False
    edit: bool = False
    create: bool = False
    delete: bool = False
    done: bool = False
    users: bool = False
    admins: bool = False
    subordinate_state: typing.Optional[bool] = None
    subordinate_index: typing.Optional[int] = None


class Inline:
    @classmethod
    async def add(cls, depth: int, user_groups: typing.List[str], translate_groups: typing.Optional[typing.List[str]] = None):
        if not translate_groups: translate_groups = list(user_groups)
        builder = InlineKeyboardBuilder()

        [eval(f'''builder.button(text=f"Добавить {translate_groups[n]}а", callback_data=SuperUserMenu({group}=True))''',
              {'builder': builder, 'SuperUserMenu': SuperUserMenu})
         for n, group in enumerate(user_groups)]

        builder.button(text="Назад", callback_data=SuperUserMenu(depth=depth-1, add_group=False))
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    async def main(cls, user: types.User, depth: int = 0):
        builder = InlineKeyboardBuilder()
        if privileged_users[user.id]['update_permissions_subgroup'] or privileged_users[user.id]['super_user']:
            builder.button(text="Группы", callback_data=SuperUserMenu(depth=depth, add_group=True))
        if privileged_users[user.id]['update_user_group'] or privileged_users[user.id]['super_user']:
            builder.button(text="Пользователи", callback_data=SuperUserMenu(depth=depth, add_user=True))
        builder.button(text="Назад", callback_data=MainMenu(main=True))
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    async def permissions(cls, depth: int, add_group: bool = True):
        builder = InlineKeyboardBuilder()
        builder.button(text="Создать", callback_data=SuperUserMenu(depth=depth+1, add_group=add_group, create=True))
        builder.button(text="Изменить", callback_data=SuperUserMenu(depth=depth+1, add_group=add_group, edit=True))
        builder.button(text="Удалить", callback_data=SuperUserMenu(depth=depth+1, add_group=add_group, delete=True))
        builder.button(text="Назад", callback_data=SuperUserMenu(depth=depth, add_group=False, edit=False,
                                                                 delete=False, create=False))
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
                               callback_data=SuperUserMenu(
                                   depth=depth+1, add_group=True, index_editable_group=num, edit=edit, delete=delete,
                                   permissions_editable=permissions_editable, subordinate_editable=subordinate_editable))

        builder.button(text="Назад", callback_data=SuperUserMenu(
            depth=depth-1, add_group=True, edit=True, delete=False
        ))

        create_order_button(builder, buttons=sub_groups, custom_buttons=1)

        return builder.as_markup()

    @classmethod
    async def choose_group(cls, depth: int, sub_groups: typing.Iterable,
                           temp_groups: typing.Iterable,
                           menu: typing.Callable = SuperUserMenu,
                           index_editable_group: typing.Optional[int] = None,
                           is_admins: typing.Optional[bool] = None,
                           is_users: typing.Optional[bool] = None,
                           add_group: bool = True,
                           add_user: bool = False,
                           id: int = -1, **kwargs):

        builder = InlineKeyboardBuilder()

        for num, group in enumerate(sub_groups):
            subordinate_state = group in temp_groups
            builder.button(text=f"{'🔴 Убрать' if subordinate_state else '🟢 Добавить'} {group}",
                           callback_data=menu(
                               depth=depth, add_group=True, index_editable_group=index_editable_group, edit=True,
                               subordinate_editable=True, subordinate_index=num, admins=is_admins, users=is_users,
                               subordinate_state=not subordinate_state, id=id
                           ))

        builder.button(text="Готово", callback_data=menu(
            depth=depth - 1, add_group=add_group, edit=True, subordinate_editable=True, done=True))
        builder.button(text="Назад", callback_data=menu(depth=depth - 1, add_group=True, edit=True,
                                                        subordinate_editable=True, id=id,
                                                        admins=is_admins, users=is_users,))

        create_order_button(builder, buttons=sub_groups, custom_buttons=2)

        return builder.as_markup()

    @classmethod
    async def group_permission_edit(cls, depth: int, temp_groups: dict, editable_group: str, index_editable_group: int,
                                    add_group: bool, edit: bool, delete: bool, user_id: int):
        builder = InlineKeyboardBuilder()
        num: int = 0
        count_rows = len(temp_groups[editable_group])

        for permission_name, permission_state in temp_groups[editable_group].items():
            if permission_name == 'subordinate_groups': continue
            if not privileged_users[user_id]['super_user']:
                if not privileged_users[user_id]['update_permissions_subgroup']: break
                if (permission_name == 'add_or_delete_group' and not privileged_users[user_id]['add_or_delete_group'])\
                   or (permission_name == 'update_user_group' and not privileged_users[user_id]['update_user_group']):
                    count_rows -= 1
                    continue
            builder.button(text=f'{permission_name} ({"А" if permission_state else "Н"})',
                           callback_data=SuperUserMenu(depth=depth, add_group=add_group,
                                                       index_editable_group=index_editable_group, edit=edit,
                                                       permission_name=num, permission_state=permission_state,
                                                       permissions_editable=True, delete=delete))
            num += 1

        builder.button(text="Готово", callback_data=SuperUserMenu(
            depth=depth-1, add_group=add_group, edit=True, permissions_editable=True, done=True))

        builder.button(text="Назад", callback_data=SuperUserMenu(
                               depth=depth-1, add_group=add_group, permissions_editable=True, edit=True))

        create_order_button(builder, buttons=count_rows, custom_buttons=2)

        return builder.as_markup()

    @classmethod
    async def group_select_for_edit(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Права группы", callback_data=SuperUserMenu(
            depth=depth+1, edit=True, add_group=True, permissions_editable=True))
        builder.button(text="Наследование", callback_data=SuperUserMenu(
            depth=depth+1, edit=True, add_group=True, subordinate_editable=True))

        builder.button(text="Назад", callback_data=SuperUserMenu(depth=depth-1, edit=True, add_group=True,))

        create_order_button(builder, buttons=2)
        return builder.as_markup()

    @classmethod
    async def finish(cls, depth: int, add_group: bool = False, add_user: bool = False, create:bool = False,
                     edit:bool = False, delete:bool = False):
        builder = InlineKeyboardBuilder()
        builder.button(text="Готово", callback_data=SuperUserMenu(depth=depth, add_user=add_user, add_group=add_group,
                                                                  create=create, edit=edit, delete=delete, done=True))

        builder.add(await cancel("Отмена"))
        return builder.as_markup()

    @classmethod
    async def confirm_to_delete(cls, depth: int):
        builder = InlineKeyboardBuilder()

        builder.button(
            text="Готово",
            callback_data=SuperUserMenu(
                depth=depth+1, add_group=True, delete=True,
                done=True
            ))
        print(depth)
        builder.button(text='Назад', callback_data=SuperUserMenu(depth=depth-1, add_group=True, delete=True))

        return builder.as_markup()

    @classmethod
    async def close(cls):
        builder = InlineKeyboardBuilder().add(await cancel("Отмена"))
        return builder.as_markup()

    @classmethod
    async def work_with_users(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Список", callback_data=UserSuperUserMenu(depth=depth+1))
        builder.button(text="Добавить", callback_data=UserSuperUserMenu(depth=depth, create=True))
        builder.button(text="Назад", callback_data=SuperUserMenu(depth=depth-1))
        builder.adjust(2, 1)
        return builder.as_markup()

    @classmethod
    async def what_users(cls, depth: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Пользователи", callback_data=UserSuperUserMenu(depth=depth+1, users=True))
        builder.button(text="Сотрудники", callback_data=UserSuperUserMenu(depth=depth+1, admins=True))
        builder.button(text="Назад", callback_data=UserSuperUserMenu(depth=depth - 1))
        builder.adjust(2, 1)
        return builder.as_markup()

    @classmethod
    async def get_users_list(cls, depth: int, user_list: typing.Iterable[types.User | dict], is_users: bool = False, is_admins: bool = False):
        builder = InlineKeyboardBuilder()
        is_json = False
        temp = iter(user_list)
        if isinstance(next(temp), dict): is_json = True
        del temp

        for num, user in enumerate(user_list):
            builder.button(text=user.full_name if not is_json else f"{user['first_name']} {user['last_name']}",
                           callback_data=UserSuperUserMenu(
                depth=depth+1, id=num, users=is_users, admins=is_admins
            ))

        builder.button(text="Назад", callback_data=UserSuperUserMenu(depth=depth-1, users=False, admins=False))
        builder.adjust(2)
        return builder.as_markup()

    # @classmethod
    # async def edit_user(cls, depth: int, sub_groups: list, callback_data: UserSuperUserMenu):
    #     builder = InlineKeyboardBuilder()
    #     for group in sub_groups:
    #         builder.button(text=group, callback_data=UserSuperUserMenu(
    #             id=callback_data.id, users=callback_data.users, admins=callback_data.admins
    #         ))
    #
    #     builder.button(text="Назад", callback_data=UserSuperUserMenu(
    #         depth=depth, users=callback_data.users, admins=callback_data.admins,
    #     ))
    #     return builder.as_markup()
