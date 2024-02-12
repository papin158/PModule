__author__ = b'papin158'

from aiogram import Router, types, html, F
from aiogram.fsm.context import FSMContext
from root.config.config import faq_list, faq_group_list
from root.utils.databases import dbcommands
from root.utils.fsm.faq import FAQ
from root.keyboards.FAQ.FAQ_keyboard import FAQ_CD, Inline_FAQ, FAQGroup
from root.keyboards.FAQ.admin.fsm_state import FAQ_Edit_CB, default_cancel, Inline, faq_finish
from aiogram.fsm.state import State

router = Router()


async def faq_menu_edit(call: types.CallbackQuery, depth, real_depth, state, **kwargs):
    context = await state.get_data()
    gl = context['str_group_list'] if context.get('str_group_list') else ''
    group_list = eval(f"faq_group_list{gl}")
    await call.message.edit_text(
        "Что нужно изменить",
        reply_markup=await Inline_FAQ.get_faq_group(
            func_depth=depth, edit=True, group_list=group_list, depth=real_depth))


async def faq_what_edit(call: types.CallbackQuery, depth, **kwargs):
    await call.message.edit_text("Выберите, что нужно изменить", reply_markup=await Inline_FAQ.FAQ_edit(depth=depth))


async def faq_edit(call: types.CallbackQuery, state: FSMContext, bot,  **kwargs):
    context = await state.get_data()
    exe = compile(f'''async def __ex(call, state, context, bot):
    del_mes = context.get('del_mes')
    if not del_mes:
        del_mes = await call.message.answer(reply_markup=await default_cancel(), text='_')
    else: del_mes = types.Message.model_validate_json(context.get('del_mes')).as_(bot)

    mes = await call.message.edit_text("Введите новое содержимое для этого пункта", 
    reply_markup=await Inline.FAQ_create(0, {context['editable_parameter']}=True, text='К началу'))
    await state.update_data(del_mes=del_mes.model_dump_json(), message_for_edit=mes.model_dump_json())
    await state.set_state({context['new_state']})''', '', 'exec', optimize=1)
    exec(exe)
    return await locals()['__ex'](call, state, context, bot)


async def set_new_faq(message: types.Message | types.CallbackQuery,
                      state: FSMContext, bot,
                      depth=2, **kwargs):
    if isinstance(message, types.CallbackQuery): message = message.message
    text = message.text
    await message.delete()
    context = await state.get_data()
    group_list = context['str_group_list'] if context.get('str_group_list') else ''
    group = context['group'] if context.get('group') else ''
    group_list = eval(compile(f"faq_group_list{group_list}", filename='faq_edit.py', mode='eval', optimize=2))
    is_answer = is_question = False
    question = group
    answer = group_list[question]['answer']

    if context['text_type_edit'] == 'answer':
        is_answer = True
    else:
        is_question = True

    second_arg = 'answer' if not is_answer else 'question'

    pre_text = f"{html.bold('Текст:')} \r\n{html.pre(answer if is_answer else question)}\r\n\n" \
               f"{html.bold('Будет изменено на:')} \r\n{html.pre(text)}"
    exe = f'''async def __ex(message, state, depth, context, pre_text, text, bot, answer, question, is_question):
    message_for_edit = types.Message.model_validate_json(context['message_for_edit']).as_(bot)
    await message_for_edit.edit_text(pre_text,
        reply_markup=await Inline.FAQ_finish(depth=depth, {context['editable_parameter']}=True, text="Изменить всё"))

    await state.update_data({context['text_type_edit']}=text, {second_arg}=answer if not is_question else question)
'''
    exec(exe)
    return await locals()['__ex'](message, state, depth, context, pre_text, text, bot, answer, question, is_answer)


async def finish(call: types.CallbackQuery, depth, state: FSMContext, bot,  **kwargs):
    # sql = dbcommands.FAQ_SQLRequests()
    context = await state.get_data()
    first_group = f"[\'{context['group_list'][0]}\']" if context.get('group_list') and len(context['group_list']) > 0 else ''
    group = context['group'] if context.get('group') else ''
    bruh = f"faq_group_list{context['str_group_list'] if context.get('str_group_list') else ''}" \
           f".pop(group)\n" \
           f"faq_group_list.update(faq_group_list)"
    exec(bruh)
    # await sql.delete(question=faq_list[context['id']]['question'])
    await faq_finish(call, depth=depth, state=state, bot=bot)


async def redistributor(call: types.CallbackQuery | types.Message, state: FSMContext, bot,
                        callback_data: FAQ_Edit_CB | FAQGroup | None = None):
    f_depth = 3
    real_depth = (await state.get_data()).get('real_depth')
    if isinstance(callback_data, FAQGroup):
        await state.update_data(group=callback_data.group)
        f_depth = callback_data.func_depth
        real_depth = callback_data.depth
        # print(callback_data.group)
    elif isinstance(callback_data, FAQ_Edit_CB):
        f_depth = callback_data.depth
        if callback_data.answer_only:
            await state.update_data(text_type_save="question", text_type_edit="answer",
                                    editable_parameter="answer_only", new_state='FAQ.ONLY_ANSWER')
        else:
            await state.update_data(text_type_save="answer", text_type_edit="question",
                                    editable_parameter="title_only", new_state='FAQ.ONLY_QUESTION')
    else:
        callback_data = type("temp", (), {"depth": 3})
    depth = {
        0: faq_menu_edit,
        1: faq_what_edit,
        2: faq_edit,
        3: set_new_faq,
        4: finish,
    }
    current_func = depth[f_depth]

    await current_func(
        call,
        depth=f_depth,
        real_depth=real_depth,
        state=state,
        bot=bot
    )


router.message.register(redistributor, FAQ.ONLY_QUESTION)
router.message.register(redistributor, FAQ.ONLY_ANSWER)
router.callback_query.register(redistributor, FAQ_Edit_CB.filter(F.title_only.is_(True) | F.answer_only.is_(True)))
router.callback_query.register(redistributor, FAQGroup.filter(F.edit.is_(True)))

