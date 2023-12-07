from aiogram import types, filters, F, html, Router
from root.config import privileged_users, group_subordinate
from root.keyboards.super_users.super_users import SuperUserMenu
import itertools

router = Router()


async def admin_menu(call: types.CallbackQuery, callback_data: SuperUserMenu):
    user_have_permission_for_addable_other_privileged_user: bool = False
    for user_group, subgroup in itertools.chain(group_subordinate[0]):
        if user_group == subgroup['user_group']: user_have_permission_for_addable_other_privileged_user = True


router.callback_query.register(admin_menu, SuperUserMenu.filter())
