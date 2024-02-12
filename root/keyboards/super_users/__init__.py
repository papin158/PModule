import typing, math
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from root.keyboards import MainMenu
from root.keyboards.FAQ.admin.fsm_state import cancel
from root.keyboards import contact_support
from root.config import privileged_users, admin_callbacks

from . import super_users
from . import groups
from . import users

SuperUserMenu = super_users.SuperUserMenu
GroupEditable = groups.GroupEditable
UserEditable = users.UserEditable

admin_callbacks.update(("admin_menu", "group_edit", "user_editable"))


class Inline(groups.Inline, users.Inline):
    @classmethod
    async def add(cls, depth: int, user_groups: typing.List[str],
                  translate_groups: typing.Optional[typing.List[str]] = None):
        if not translate_groups: translate_groups = list(user_groups)
        builder = InlineKeyboardBuilder()

        [eval(f'''builder.button(text=f"Добавить {translate_groups[n]}а", callback_data=SuperUserMenu({group}=True))''',
              {'builder': builder, 'SuperUserMenu': super_users.SuperUserMenu})
         for n, group in enumerate(user_groups)]

        builder.button(text="Назад", callback_data=super_users.SuperUserMenu(depth=depth - 1))
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    async def main(cls, user: types.User, depth: int = 0):
        builder = InlineKeyboardBuilder()
        if privileged_users[user.id]['update_permissions_subgroup'] or privileged_users[user.id]['super_user']:
            builder.button(text="Группы", callback_data=groups.GroupEditable(depth=depth))
        if privileged_users[user.id]['update_user_group'] or privileged_users[user.id]['super_user']:
            builder.button(text="Пользователи", callback_data=UserEditable(depth=depth, add_user=True))
        if privileged_users[user.id]['update_faq'] or privileged_users[user.id]['super_user']:
            builder.button(text="Ожидающие поддержки", callback_data=contact_support.SupportContact(coord=0))
        builder.button(text="Назад", callback_data=MainMenu(main=True))
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    async def confirm(cls, depth: int, create: bool = False,
                      add_group: bool = False, menu=super_users.SuperUserMenu,
                      delete: bool = False, id=-1, ban_list=False,
                      ban: bool = False):
        builder = InlineKeyboardBuilder()

        builder.button(
            text="Готово",
            callback_data=menu(
                depth=depth - 1, add_group=add_group, delete=delete, ban=ban, create=create, id=id,
                done=True, ban_list=ban_list
            ))
        builder.button(text='Назад', callback_data=menu(
            depth=depth - 1, add_group=add_group, delete=delete, ban=ban, create=create, id=id,
            ban_list=ban_list
        ))

        return builder.as_markup()

    @classmethod
    async def close(cls):
        builder = InlineKeyboardBuilder().add(await cancel("Отмена"))
        return builder.as_markup()



