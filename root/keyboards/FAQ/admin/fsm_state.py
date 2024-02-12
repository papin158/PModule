import typing, asyncio
from functools import wraps

from aiogram import types, html, F, filters, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from root.utils.databases import dbcommands
from root import config
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from root.utils.execute import always_answer, execute
from root.config import faq_group_list


class FAQ_Edit_CB(CallbackData, prefix='faq_edit_state'):
    __slots__ = ()
    id: typing.Optional[int] = None
    depth: int = 0
    title_only: bool = False
    answer_only: bool = False


def fsm_state_close(FSMSTATE, router):
    exe = compile(f'''def __ex(FSMSTATE, router):
    router.message.register(state_cancel, F.text.lower() == 'экстренно_закрыть', filters.StateFilter(FSMSTATE))
    router.callback_query.register(state_cancel, F.data == 'close_state', filters.StateFilter(FSMSTATE))''',
                  '', 'exec', optimize=1)
    exec(exe)
    return locals()['__ex'](FSMSTATE, router)


async def state_cancel(message: types.CallbackQuery, state: FSMContext, bot: Bot,
                       back: typing.Optional[ReplyKeyboardMarkup] = None):
    context = await state.get_data()
    del_mes = context.get('del_mes')
    message_for_edit = context.get('message_for_edit')
    if del_mes: await types.Message.model_validate_json(del_mes).as_(bot).delete()

    if isinstance(message, types.CallbackQuery):
        call = message
        mes = await call.message.edit_text("Действие отменено", reply_markup=None)
        await asyncio.sleep(1)
        await mes.delete()
    else:
        await message.delete()
        if message_for_edit:
            await types.Message.model_validate_json(message_for_edit).as_(bot).\
                edit_text("экстренно закрыто", reply_markup=None)
            await asyncio.sleep(1)
            await types.Message.model_validate_json(message_for_edit).as_(bot).delete()
    await state.clear()


def fsm_final(text, del_mes: str = 'del_mes', message_for_edit: str = 'message_for_edit'):
    """

    :param text: Текст, который будет отправлен при изменении текста сообщения.
    :param del_mes: Сообщение в FSM-state должно быть удалено, как "экстренное закрытие состояния"
    :param message_for_edit: Сообщение, которое должно изменяться
    :return:
    """
    def fun_decor(func):
        @wraps(func)
        async def wrapper(call, state: FSMContext, bot, *args, **kwargs):
            context = await state.get_data()
            kwargs.update(state=state, context=context, bot=bot)
            result = await func(call, *args, **kwargs)
            if context[del_mes] and bot: await (types.Message.model_validate_json(context[del_mes]).as_(bot)).delete()
            await types.Message.model_validate_json(context[message_for_edit]).as_(bot).edit_text(html.bold(text))
            await state.clear()
            await asyncio.sleep(3)
            await (types.Message.model_validate_json(context[message_for_edit]).as_(bot)).delete()
            return result

        return wrapper
    return fun_decor


# def fsm_start(text: str, fsm_state: State, markup=None, without_exit=False, p_f_c_b=None, is_i=False):
#     # "p_f_c_b" это "params_for_callback_button" или параметры для параметра markup
#     if p_f_c_b is None: p_f_c_b = dict()
#
#     def func_decor(func):
#         @wraps(func)
async def fsm_start(
        message: types.CallbackQuery | types.Message, text, fsm_state: State,
        state: FSMContext, markup=None, p_f_c_b: dict = None, without_exit=False,  *args, **kwargs):
    callback_data = kwargs.get('callback_data')
    if p_f_c_b is None: p_f_c_b = {}
    bot: Bot = kwargs.get('bot')
    depth = kwargs.get('depth')
    context = await state.get_data()
    message_for_edit = context.get('message_for_edit')
    del_mes = context.get('del_mes')

    if not depth:
        depth = int(callback_data.depth) if hasattr(callback_data, 'depth') else 0

    if message_for_edit: message_for_edit = types.Message.model_validate_json(message_for_edit).as_(bot)

    if 'depth' not in p_f_c_b: p_f_c_b.update(depth=depth)

    if not without_exit:
        if not del_mes:
            del_mes = await always_answer(message, reply_markup=await default_cancel(), text='_', )
        else:
            del_mes = types.Message.model_validate_json(del_mes).as_(bot)

    mes = await execute(message, text,
                        reply_markup=await markup(**p_f_c_b) if markup else None,
                        schrodinger_message=message_for_edit)

    if isinstance(message, types.Message) and message.from_user.id != bot.id and context: await message.delete()
    await state.update_data(message_for_edit=mes.model_dump_json(), depth=depth,
                            del_mes=del_mes.model_dump_json() if not without_exit else None)
    kwargs.update(state=state, bot=bot, depth=depth)
    await state.set_state(fsm_state)


@fsm_final("ЧАВО/ЧЗВ добавлено")
async def faq_finish(call: types.CallbackQuery, state: FSMContext, context: dict, **kwargs):
    group_list = context.get('group_list') if context.get('group_list') else []
    length = len(group_list)
    first_element = f"[\'{group_list[0]}\']" if length > 0 else ''
    group_list = [f"[\'{group}\']" for group in group_list]
    group_list = ''.join(group_list)
    bruh = f'faq_group_list{group_list}.update({{context["question"]: {{"answer": context["answer"]}}}})\n' \
           f'faq_group_list.update(faq_group_list)'
    exec(bruh)


async def cancel(text) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data='close_state')


async def default_cancel():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="экстренно_закрыть")]])


class Inline:
    __slots__ = ()

    @classmethod
    async def final_edit(cls, text: str, title_only: bool = False, answer_only: bool = False):
        return InlineKeyboardButton(text=text,
                                    callback_data=FAQ_Edit_CB(depth=0, title_only=title_only,
                                                              answer_only=answer_only).pack())

    @classmethod
    async def edit_prev_str(cls, depth, title_only: bool = False, answer_only: bool = False):
        return InlineKeyboardButton(text='Изменить прошлую строку', callback_data=FAQ_Edit_CB(
            depth=depth - 1, title_only=title_only, answer_only=answer_only).pack())

    @classmethod
    async def FAQ_finish(cls, depth, text: str, title_only: bool = False, answer_only: bool = False):
        builder = InlineKeyboardBuilder()
        builder.button(text='Готово', callback_data=FAQ_Edit_CB(depth=depth + 1, title_only=title_only,
                                                                answer_only=answer_only))
        if depth != 0:
            if not (answer_only or title_only): builder.row(await cls.final_edit(title_only=title_only, text=text,
                                                            answer_only=answer_only))
            builder.row(await cls.edit_prev_str(depth, title_only=title_only, answer_only=answer_only))
        builder.row(await cancel("Отменить"))

        return builder.as_markup()

    @classmethod
    async def FAQ_create(cls, depth, text: str, title_only: bool = False, answer_only: bool = False):
        builder = InlineKeyboardBuilder()
        cancel_button = await cancel("Отменить")
        if depth != 0:
            builder.row(await cls.edit_prev_str(depth, title_only=title_only, answer_only=answer_only))
            if not (answer_only or title_only): builder.row(await cls.final_edit(title_only=title_only, text=text, answer_only=answer_only))
        builder.row(cancel_button)
        return builder.as_markup()

