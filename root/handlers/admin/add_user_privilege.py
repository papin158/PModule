from aiogram import F, Router

from root.keyboards.FAQ.admin.fsm_state import fsm_state_close
from .groups_manages import *
from .user_manage import *
from root.keyboards.super_users import SuperUserMenu


router = Router()


async def admin_menu(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите, что редактировать", reply_markup=await Inline.main(call.from_user))
    await state.clear()
    await call.answer()


fsm_state_close(AddNewGroup, router)

router.message.register(send_new_group, AddNewGroup.NAME_NEW_GROUP)
router.message.register(find_user, AddNewGroup.FIND_USER)
router.callback_query.register(create_group, GroupEditable.filter(
    F.create.is_(True) &
    F.done.is_(True)
))

router.callback_query.register(ban, UserEditable.filter(
    F.ban.is_(True) &
    F.done.is_(True)
))

router.callback_query.register(add_group, GroupEditable.filter(
    F.create.is_(True)
))

router.callback_query.register(group_redistributor, GroupEditable.filter())

router.callback_query.register(user_distributor, UserEditable.filter())
router.callback_query.register(admin_menu, SuperUserMenu.filter())
