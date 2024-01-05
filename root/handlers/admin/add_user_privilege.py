from aiogram import F, Router

from root.keyboards.FAQ.admin.fsm_state import fsm_state_close
from .groups_manages import *
from .user_manage import *


router = Router()


async def admin_menu(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, **kwargs):
    await call.message.edit_text("Выберите, что редактировать", reply_markup=await Inline.main(call.from_user))
    await state.clear()
    await call.answer()


fsm_state_close(AddNewGroup, router)

router.message.register(send_new_group, AddNewGroup.NAME_NEW_GROUP)
router.callback_query.register(create_group, SuperUserMenu.filter(
    F.add_group.is_(True) &
    F.create.is_(True) &
    F.done.is_(True)
))
router.callback_query.register(add_group, SuperUserMenu.filter(
    F.add_group.is_(True) &
    F.create.is_(True)
))
router.callback_query.register(group_redistributor, SuperUserMenu.filter(
    F.add_group.is_(True) &
    F.edit.is_(True)
))
router.callback_query.register(group_redistributor, SuperUserMenu.filter(
    F.add_group.is_(True)
))


router.callback_query.register(user_distributor, UserSuperUserMenu.filter())
router.callback_query.register(user_distributor, SuperUserMenu.filter(
    F.add_user.is_(True)
))
router.callback_query.register(admin_menu, SuperUserMenu.filter())
