import typing, asyncio
from functools import wraps
from pprint import pprint

from aiogram import types, html, F, filters, Bot
from aiogram.fsm.context import FSMContext
from root.utils.databases import dbcommands
from root import config
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


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
        print("DA?")
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
            kwargs.update(context=context, bot=bot)
            result = await func(call, state, *args, **kwargs)
            if context[del_mes] and bot: await (types.Message.model_validate_json(context[del_mes]).as_(bot)).delete()
            await types.Message.model_validate_json(context[message_for_edit]).as_(bot).edit_text(html.bold(text))
            await asyncio.sleep(3)
            await (types.Message.model_validate_json(context[message_for_edit]).as_(bot)).delete()
            await state.clear()
            return result

        return wrapper
    return fun_decor


@fsm_final("ЧАВО/ЧЗВ добавлено")
async def faq_finish(call: types.CallbackQuery, state: FSMContext, context: dict, **kwargs):
    sql = dbcommands.FAQ_SQLRequests()
    faq = await sql.add(question=context['question'], answer=context['answer'])
    config.faq_list.clear()
    config.faq_list.extend(await sql.get())


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

