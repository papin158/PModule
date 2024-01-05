from aiogram import Router, types, filters, html, F
from root.keyboards.FAQ.FAQ_keyboard import FAQ_CD, Inline_FAQ, faq_list
from root.config import config
from root.utils.databases.dbcommands import FAQ_SQLRequests

router = Router()


async def get_for_delete(call: types.CallbackQuery, depth=0, the_main: bool = True, **kwargs):
    await call.message.edit_text(html.bold("Получаем список всех FAQ"),
        reply_markup=await Inline_FAQ.get_faq(depth, for_delete=True, the_main=the_main,
        user=call.from_user))


async def redistributor(call: types.CallbackQuery, callback_data: FAQ_CD):
    depth = {
        0: get_for_delete,
        1: confirm_delete,
        2: faq_delete,
    }
    current_def = depth[callback_data.depth]
    await current_def(
        call,
        depth=callback_data.depth,
        mes_id=callback_data.id,
        the_main=callback_data.the_main
    )


async def confirm_delete(call: types.CallbackQuery, depth, mes_id, **kwargs):
    if len(faq_list) > 0: text = f"{html.bold(faq_list[mes_id]['question'])} будет удалена."
    else: text = "Нечего удалять"
    await call.message.edit_text(text, reply_markup=await Inline_FAQ.confirm_to_delete_faq(
        id=mes_id, depth=depth, empty=len(faq_list) <= 0))
    await call.answer()


async def faq_delete(call: types.CallbackQuery, mes_id: int, **kwargs):
    sql = FAQ_SQLRequests()
    await call.message.edit_text(f"{html.bold(faq_list[mes_id]['question'])} удалена.")
    print(html.bold(faq_list[mes_id]['question']))
    await sql.delete(faq_list[mes_id]['question'])
    faq_list.clear()
    faq_list.extend(await sql.get())
    await call.answer()

router.message.register(get_for_delete, filters.Command("faq_delete"))
router.callback_query.register(redistributor, FAQ_CD.filter(F.for_delete))
