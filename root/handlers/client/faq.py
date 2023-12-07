from aiogram import Router, types, filters, html, F
from root.keyboards.FAQ.FAQ_keyboard import Inline_FAQ, desc, FAQ_CD
from root.utils.execute import execute, awaitable_reply_markup
from root.config.config import privileged_users

router = Router()


async def FAQ(message: types.Message | types.CallbackQuery, callback_data: FAQ_CD = None, **kwargs):
    text = f"{html.bold('Выберите интересующий Вас вопрос из списка ЧаВо/ЧЗВ/FAQ')}"
    if not callback_data:
        callback_data = {'depth'}
        if message.from_user.id in privileged_users['admins']:  # O(1) т.к. ищется хэш в set через хеш-таблицу
            callback_data.add('user')
    print(callback_data.depth)
    await execute(message, text, reply_markup=Inline_FAQ.get_faq, callback_data=callback_data,
                  advanced_args={"user": message.from_user, "the_main": True})


async def cb_FAQ(call: types.CallbackQuery, callback_data: FAQ_CD):
    is_superusers = call.from_user.id in privileged_users['admins']
    if is_superusers and callback_data.depth == 0 and callback_data.is_privileged:
        await call.message.edit_text(f"FAQ", reply_markup=await Inline_FAQ.admin_table(depth=0, user=call.from_user))
    elif callback_data.depth == 0:
        await FAQ(message=call, callback_data=callback_data)
    else:
        await call.message.edit_text(
            desc[0][callback_data.id]['answer'],
            reply_markup=await Inline_FAQ.back_to_FAQ(FAQ_CD, callback_data.depth, the_main=callback_data.the_main))
    await call.answer()

router.callback_query.register(cb_FAQ, FAQ_CD.filter(F.for_delete.is_(False) | F.for_edit.is_(False)))
router.message.register(FAQ, filters.Command("faq"))
