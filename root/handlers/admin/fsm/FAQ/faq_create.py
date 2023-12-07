import asyncio

from aiogram import types, Router, filters, html, F
from aiogram.fsm.context import FSMContext
from root.utils.fsm.faq import FAQ
from root.config.config import faq_list, R_SQL
from root.utils.databases.dbcommands import FAQ_SQLRequests
from root.keyboards.FAQ.admin.fsm_state import Inline, FAQ_Edit_CB, default_cancel, faq_finish

router = Router()


async def create_one_faq(message: types.Message | types.CallbackQuery, state: FSMContext, depth=0):
    if isinstance(message, types.CallbackQuery):
        message = message.message
        if message.from_user.id != message.bot.id: await message.delete()
        context = await state.get_data()
        await asyncio.sleep(0.2)
        if context.get('message_for_edit'): message = context['message_for_edit']
        else: del_mes = await message.answer(reply_markup=await default_cancel(), text='_')
        mes = await message.edit_text("Заголовок FAQ", reply_markup=await Inline.FAQ_create(depth, text="Изменить всё"))
        await state.update_data(message_for_edit=mes, del_mes=del_mes if not context and not context.get('del_mes') else context.get('del_mes'))
    else:
        context = await state.get_data()
        if context: return await message.delete()
        del_mes = await message.answer(reply_markup=await default_cancel(), text='_')
        await message.delete()
        mes = await message.answer("Заголовок FAQ", reply_markup=await Inline.FAQ_create(depth, text="Изменить всё"))
        await state.update_data(message_for_edit=mes, del_mes=del_mes)

    await state.set_state(FAQ.GET_QUESTION)


async def faq_get_question(message: types.Message | types.CallbackQuery, state: FSMContext, depth=1):
    if isinstance(message, types.CallbackQuery):message = message.message
    m_text = message.text
    if message.from_user.id != message.bot.id: await message.delete()

    override = ''

    for faq in faq_list[0]:
        if m_text == faq['question']: override = faq['answer']
    if override: text = f"Вопрос \"{html.code(m_text)}\" уже существует, и выглядит так {html.pre(override)} написав ответ Вы его перезапишите."
    else: text = "Напиши ответ на этот вопрос"

    context = await state.get_data()
    mes = await context['message_for_edit'].edit_text(text, reply_markup=await Inline.FAQ_create(depth,
                                                                                                 text="Изменить всё"))
    await state.update_data(question=m_text, message_for_edit=mes)
    await state.set_state(FAQ.GET_ANSWER)


async def faq_get_answer(message: types.Message | types.CallbackQuery, state: FSMContext, depth=2):
    context = await state.get_data()
    if isinstance(message, types.CallbackQuery):message = message.message
    text = message.text
    if message.from_user.id != message.bot.id: await message.delete()

    mes = await context['message_for_edit'].edit_text(
        f"Проверь правильность введённой информации:\r\n\n\n{html.bold(context['question'])}"
        f"\r\n{text}\r\n\n\nЕсли всё устраивает нажми на кнопку {html.bold('Готово')}, "
        f"если нужно что-то отредактировать {html.bold('Изменить')}, в ином случае нажми "
        f"{html.bold('Отмена')}", reply_markup=await Inline.FAQ_finish(depth, text="Изменить всё"))
    await state.update_data(answer=text, message_for_edit=mes)


async def state_cancel(message: types.CallbackQuery, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        call = message
        context = await state.get_data()
        if context.get('del_mes'): await context['del_mes'].delete()
        mes = await call.message.edit_text("Действие отменено", reply_markup=None)
        await asyncio.sleep(1)
        await mes.delete()
    else:
        context = await state.get_data()
        if context.get('del_mes'): await context['del_mes'].delete()
        await message.delete()
        if context.get('message_for_edit'): await context['message_for_edit'].edit_text("экстренно закрыто", reply_markup=None)
        await asyncio.sleep(1)
        if context.get('message_for_edit'): await context['message_for_edit'].delete()
    await state.clear()


async def settings_state(call: types.CallbackQuery, callback_data: FAQ_Edit_CB, state: FSMContext):
    depth = {
        0: create_one_faq,
        1: faq_get_question,
        2: faq_get_answer,
        3: faq_finish
    }

    current_func = depth[callback_data.depth]
    await current_func(
        call,
        state=state,
        depth=callback_data.depth
    )


router.message.register(create_one_faq, filters.Command("create_faq"))
router.message.register(state_cancel, F.text.lower() == 'экстренно_закрыть', filters.StateFilter(FAQ))
router.message.register(faq_get_question, FAQ.GET_QUESTION)
router.message.register(faq_get_answer, FAQ.GET_ANSWER)
router.callback_query.register(settings_state, FAQ_Edit_CB.filter(F.title_only.is_(False)))
router.callback_query.register(state_cancel, F.data == 'close_state', filters.StateFilter(FAQ))
