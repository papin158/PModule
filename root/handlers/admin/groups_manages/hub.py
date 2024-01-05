from aiogram import types
from aiogram.fsm.context import FSMContext

from root.keyboards.super_users.super_users import SuperUserMenu, Inline


async def manage_groups(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите действие", reply_markup=await Inline.permissions(
        depth=callback_data.depth))
