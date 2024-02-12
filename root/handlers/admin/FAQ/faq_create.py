import asyncio

from aiogram import types, Router, filters, html, F, Bot
from aiogram.fsm.context import FSMContext

from root.utils.fsm.admin_menu import AddNewGroup
from root.utils.fsm.faq import FAQ
from root.config.config import faq_list, R_SQL
from root.utils.databases.dbcommands import FAQ_SQLRequests
from root.keyboards.FAQ.admin.fsm_state import Inline, FAQ_Edit_CB, default_cancel, faq_finish, state_cancel, \
    fsm_state_close, fsm_start
from root.utils.execute import execute, always_answer

router = Router()


async def create_one_faq(message: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext, depth=0, **kwargs):
    kwargs.update(bot=bot, state=state, depth=depth)
    await fsm_start(
        message=message, text="Заголовок FAQ", fsm_state=FAQ.GET_QUESTION,
        markup=Inline.FAQ_create, p_f_c_b={'text': "Изменить всё"}, **kwargs
    )


async def faq_get_question(message: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext, depth=1):
    context = await state.get_data()
    m_text = None

    if isinstance(message, types.CallbackQuery):
        m_text = context.get('question')
        message = message.message

    m_text = message.text if not m_text else m_text

    if message.from_user.id != bot.id: await message.delete()

    override = ''

    for faq in faq_list:
        if m_text == faq['question']: override = faq['answer']
    if override: text = f"Вопрос \"{html.code(m_text)}\" уже существует, и выглядит " \
                        f"так {html.pre(override)} написав ответ Вы его перезапишите."
    else: text = "Напиши ответ на этот вопрос"

    context = await state.get_data()
    message_for_edit = types.Message.model_validate_json(context.get('message_for_edit')).as_(bot)

    mes = await message_for_edit.edit_text(text, reply_markup=await Inline.FAQ_create(depth, text="Изменить всё"))
    await state.update_data(question=m_text, message_for_edit=mes.model_dump_json())
    await state.set_state(FAQ.GET_ANSWER)


async def faq_get_answer(message: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext, depth=2):
    context = await state.get_data()
    if isinstance(message, types.CallbackQuery):message = message.message
    text = message.text
    message_for_edit = types.Message.model_validate_json(context.get('message_for_edit')).as_(bot)
    if message.from_user.id != bot.id: await message.delete()

    mes = await message_for_edit.edit_text(
        f"Проверь правильность введённой информации:\r\n\n\n{html.bold(context['question'])}"
        f"\r\n{text}\r\n\n\nЕсли всё устраивает нажми на кнопку {html.bold('Готово')}, "
        f"если нужно что-то отредактировать {html.bold('Изменить')}, в ином случае нажми "
        f"{html.bold('Отмена')}", reply_markup=await Inline.FAQ_finish(depth, text="Изменить всё"))

    await state.update_data(answer=text, message_for_edit=mes.model_dump_json())


async def settings_state(call: types.CallbackQuery, callback_data: FAQ_Edit_CB, state: FSMContext, bot):
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
        depth=callback_data.depth,
        bot=bot
    )


# fsm_state_close(FAQ, router)
router.message.register(faq_get_question, FAQ.GET_QUESTION)
router.message.register(faq_get_answer, FAQ.GET_ANSWER)
router.callback_query.register(settings_state, FAQ_Edit_CB.filter(F.title_only.is_(False)))

