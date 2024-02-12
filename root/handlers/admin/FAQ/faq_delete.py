from aiogram import Router, types, filters, html, F
from aiogram.fsm.context import FSMContext
from root.keyboards.FAQ.FAQ_keyboard import FAQGroup, Inline_FAQ, faq_list
from root.config import faq_group_list
from root.utils.databases.dbcommands import FAQ_SQLRequests

router = Router()


async def get_for_delete(call: types.CallbackQuery, state, depth, group_list, callback_data, **kwargs):
    await call.message.edit_text(
        text=html.bold("Получаем список всех FAQ"),
        reply_markup=await Inline_FAQ.get_faq_group(
            callback_data.depth, func_depth=callback_data.func_depth,
            group_list=eval(f"faq_group_list{group_list if group_list else ''}"), delete=True
        ))

    if callback_data.back:
        await state.update_data(func_depth=None)


async def redistributor(call: types.CallbackQuery, callback_data: FAQGroup, state: FSMContext):
    context = await state.get_data()
    group_list = context['str_group_list'] if context.get('str_group_list') else ''
    # fd = context.get('func_depth')
    # if not isinstance(fd, int):
    #     callback_data.func_depth = 0
    #     await state.update_data(func_depth=0)
    func_depth = {
        0: get_for_delete,
        1: confirm_delete,
        2: faq_delete,
    }
    current_def = func_depth[callback_data.func_depth]
    await current_def(
        call,
        depth=callback_data.func_depth,
        callback_data=callback_data,
        group_list=group_list,
        # the_main=callback_data.the_main,
        state=state
    )


async def confirm_delete(call: types.CallbackQuery, state, callback_data, **kwargs):
    if len(faq_list) > 0: text = f"{html.bold(callback_data.group)} будет удалена."
    else: text = "Нечего удалять"
    await call.message.edit_text(text, reply_markup=await Inline_FAQ.confirm_to_delete_faq(
        depth=callback_data.depth, group=callback_data.group, func_depth=callback_data.func_depth))
    await call.answer()


async def faq_delete(call: types.CallbackQuery, callback_data: FAQGroup, state: FSMContext, **kwargs):
    context = await state.get_data()
    group_list = context.get('group_list') if context.get('group_list') else []
    length = len(group_list)
    first_element = f"[\'{group_list[0]}\']" if length > 0 else ''
    group_list = [f"[\'{group}\']" for group in group_list]
    group_list = ''.join(group_list)
    bruh = f'faq_group_list{group_list}.pop(callback_data.group)\n' \
           f'faq_group_list{first_element} = faq_group_list{first_element}'
    exec(bruh)
    await call.message.edit_text(
        f"{html.bold(callback_data.group)} удалена.",
        reply_markup=await Inline_FAQ.get_faq_group(
            callback_data.depth, group_list=eval(f"faq_group_list{group_list if group_list else ''}")
        ))
    await call.answer()

router.message.register(get_for_delete, filters.Command("faq_delete"))
router.callback_query.register(redistributor, FAQGroup.filter(F.delete))
