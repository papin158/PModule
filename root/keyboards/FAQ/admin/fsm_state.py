import typing, asyncio
from aiogram import types, html
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


async def faq_finish(call: types.CallbackQuery, state: FSMContext, **kwargs):
    context = await state.get_data()
    sql = dbcommands.FAQ_SQLRequests()
    faq = await sql.add(question=context['question'], answer=context['answer'])
    config.faq_list[0] = await sql.get()
    if context['del_mes']: await context['del_mes'].delete()
    await context['message_for_edit'].edit_text(html.bold("ЧАВО/ЧЗВ добавлено"))
    await asyncio.sleep(3)
    if context['message_for_edit']: await context['message_for_edit'].delete()
    await state.clear()


async def cancel(text):
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

