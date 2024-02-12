from aiogram import types
from aiogram.fsm.context import FSMContext

from ....keyboards.super_users import GroupEditable, Inline


async def manage_groups(call: types.CallbackQuery, callback_data: GroupEditable, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите действие", reply_markup=await Inline.permissions(
        depth=callback_data.depth))
