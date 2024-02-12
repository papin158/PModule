from .edit_user import *
from .add_user import *
from .ban_user import *


async def user_distributor(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, bot: Bot):
    user_depth = {
        0: manage,
        1: user_group_selection,
        2: add_user if callback_data.create else ban if callback_data.ban else user_select,
        3: get_method
    }

    await user_depth[callback_data.depth](
        call,
        callback_data=callback_data,
        state=state,
        bot=bot
    )


async def manage(call: types.CallbackQuery, callback_data: UserEditable, state: FSMContext, **kwargs):
    text = "Выберите действие"
    perem_iteration.i = None
    await state.clear()
    await call.message.edit_text(text, reply_markup=await Inline.work_with_users(0))
