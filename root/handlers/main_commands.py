from aiogram import types, Router, filters, F

from root.config import privileged_users, pool
from root.keyboards import MainMenu, main_keyboard
from root.keyboards.super_users.super_users import SuperUserMenu
from root.utils.execute import execute
from app import get_user

__all__ = [

    "router"

    ]

router = Router()


async def start_method(message: types.Message):
    await get_user(message.from_user)
    await message.answer(f"Привет друг")


async def account(message: types.Message | types.CallbackQuery, callback_data: MainMenu = None,
                  command: filters.CommandObject = None):
    text = "Выберите настройку"
    admin_menu = None
    puser = privileged_users.get(message.from_user.id) if message.from_user else None
    if puser:  # and (puser.get('update_permissions_subgroup') or puser.get('update_user_group') or puser.get('super_user')):
        admin_menu = SuperUserMenu()
    await execute(message, text, reply_markup=await main_keyboard(admin_menu))


async def menu_cancel(message: types.Message | types.CallbackQuery, callback_data: MainMenu = None):
    await execute(message, "Действие отменено", reply_markup=None)


async def say_hello(message: types.Message):
    await message.answer("Дароу братка")

router.message.register(say_hello, filters.Command("start"), F.from_user.id.in_(privileged_users))
router.message.register(start_method, filters.Command("start"))
router.callback_query.register(account, MainMenu.filter(F.main))
router.callback_query.register(menu_cancel, MainMenu.filter(F.cancel))
router.message.register(account, filters.Command('account'))
