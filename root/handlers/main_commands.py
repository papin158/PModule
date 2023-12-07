from aiogram import types, Router, filters, F
from root.keyboards import MainMenu, main_keyboard
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
    if isinstance(message, types.CallbackQuery):
        call = message
        if callback_data.main:
            await call.message.edit_text(text, reply_markup=await main_keyboard())
        else:
            await call.message.edit_text("Настройка завершена", reply_markup=None)
        await call.answer()
    else:
        await message.answer(text, reply_markup=await main_keyboard())


async def menu_cancel(message: types.Message | types.CallbackQuery, callback_data: MainMenu = None):
    await execute(message, "Действие отменено", reply_markup=None)

router.message.register(start_method, filters.Command("start"))
router.callback_query.register(account, MainMenu.filter(F.main))
router.callback_query.register(menu_cancel, MainMenu.filter(F.cancel))
router.message.register(account, filters.Command('account'))
