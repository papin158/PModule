from aiogram import Router, types, filters, F
from root.config.config import privileged_users
from root.keyboards.FAQ.FAQ_keyboard import Inline_FAQ, Admin_FAQ_CD
from . import faq_delete
from . import faq_edit
from . import faq_create
from . import faq_mov

router = Router()


async def admin_advanced_menu(call: types.CallbackQuery, callback_data: Admin_FAQ_CD):
    await call.message.edit_text(f"FAQ", reply_markup=await Inline_FAQ.admin_table(depth=0, user=call.from_user))

router.callback_query.register(admin_advanced_menu, Admin_FAQ_CD.filter())
router.include_routers(faq_delete.router, faq_edit.router, faq_create.router, faq_mov.router)
