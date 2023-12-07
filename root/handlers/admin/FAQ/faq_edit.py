from aiogram import Router, types, html, F
from aiogram.fsm.context import FSMContext
from root.config.config import faq_list
from root.utils.databases import dbcommands
from root.utils.fsm.faq import FAQ
from root.keyboards.FAQ.FAQ_keyboard import FAQ_CD, Inline_FAQ
from root.keyboards.FAQ.admin.fsm_state import FAQ_Edit_CB, default_cancel, Inline, faq_finish
from aiogram.fsm.state import State

router = Router()


async def faq_menu_edit(call: types.CallbackQuery, depth, **kwargs):
    await call.message.edit_text("Что нужно изменить",
                                 reply_markup=await Inline_FAQ.get_faq(depth=depth, for_edit=True,
                                                                       is_privileged=True, user=call.from_user))


async def faq_what_edit(call: types.CallbackQuery, depth, **kwargs):
    await call.message.edit_text("Выберите, что нужно изменить", reply_markup=await Inline_FAQ.FAQ_edit(depth=depth))


async def faq_edit(call: types.CallbackQuery, state: FSMContext,  **kwargs):
    context = await state.get_data()
    exe = compile(f'''async def __ex(call, new_state, state, context):
    del_mes = context.get('del_mes')
    if not del_mes:
        del_mes = await call.message.answer(reply_markup=await default_cancel(), text='_')

    mes = await call.message.edit_text("Введите новое содержимое для этого пункта", 
    reply_markup=await Inline.FAQ_create(0, {context['editable_parameter']}=True, text='К началу'))
    await state.update_data(del_mes=del_mes, message_for_edit=mes)
    await state.set_state(new_state)''', '', 'exec', optimize=1)
    exec(exe)
    return await locals()['__ex'](call, context['new_state'], state, context)


async def set_new_faq(message: types.Message | types.CallbackQuery,
                      state: FSMContext,
                      depth=2, **kwargs):
    if isinstance(message, types.CallbackQuery): message = message.message
    text = message.text
    await message.delete()
    context = await state.get_data()

    pre_text = f"{html.bold('Текст:')} \r\n{html.pre(faq_list[0][context['id']][context['text_type_edit']])}\r\n\n" \
               f"{html.bold('Будет изменено на:')} \r\n{html.pre(text)}"

    exe = f'''async def __ex(message, state, depth, context, pre_text, text):
    await context['message_for_edit'].edit_text(pre_text,
        reply_markup=await Inline.FAQ_finish(depth=depth, {context['editable_parameter']}=True, text="Изменить всё"))

    await state.update_data({context['text_type_save']}=faq_list[0][context['id']][context['text_type_save']], {context['text_type_edit']}=text)
'''
    exec(exe)
    return await locals()['__ex'](message, state, depth, context, pre_text, text)


async def finish(call, depth, state: FSMContext,  **kwargs):
    sql = dbcommands.FAQ_SQLRequests()
    context = await state.get_data()
    await sql.delete(question=faq_list[0][context['id']]['question'])
    await faq_finish(call, depth=depth, state=state)


async def redistributor(call: types.CallbackQuery | types.Message, state: FSMContext,
                        callback_data: FAQ_Edit_CB | FAQ_CD | None = None):
    if isinstance(callback_data, FAQ_CD): await state.update_data(id=callback_data.id)
    elif isinstance(callback_data, FAQ_Edit_CB):
        if callback_data.answer_only:
            await state.update_data(text_type_save="question", text_type_edit="answer",
                                    editable_parameter="answer_only", new_state=FAQ.ONLY_ANSWER)
        else:
            await state.update_data(text_type_save="answer", text_type_edit="question",
                                    editable_parameter="title_only", new_state=FAQ.ONLY_QUESTION)
    else:
        callback_data = type("temp", (), {"depth": 3})
    depth = {
        0: faq_menu_edit,
        1: faq_what_edit,
        2: faq_edit,
        3: set_new_faq,
        4: finish,
    }
    current_func = depth[callback_data.depth]

    await current_func(
        call,
        depth=callback_data.depth,
        state=state
    )


router.message.register(redistributor, FAQ.ONLY_QUESTION)
router.message.register(redistributor, FAQ.ONLY_ANSWER)
router.callback_query.register(redistributor, FAQ_Edit_CB.filter(F.title_only.is_(True) | F.answer_only.is_(True)))
router.callback_query.register(redistributor, FAQ_CD.filter(F.for_edit.is_(True)))

