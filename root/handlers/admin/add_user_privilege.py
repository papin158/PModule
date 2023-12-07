from aiogram import types, filters, F, html, Router
from root.config import privileged_users
from root.keyboards.super_users.super_users import SuperUserMenu

router = Router()


async def admin_menu(call: types.CallbackQuery, callback_data: SuperUserMenu):
    pass


router.callback_query.register(admin_menu, SuperUserMenu.filter())
