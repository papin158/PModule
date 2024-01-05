from .edit_user import *

from root.keyboards.super_users.super_users import SuperUserMenu, Inline


async def user_distributor(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, bot: Bot):
    user_depth = {
        0: manage,
        1: user_group_selection,
        2: user_select,
        3: get_method
    }

    await user_depth[callback_data.depth](
        call,
        callback_data=callback_data,
        state=state,
        bot=bot
    )


async def manage(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, **kwargs):
    text = "Выберите действие"
    await call.message.edit_text(text, reply_markup=await Inline.work_with_users(0))
