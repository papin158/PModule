import math
from collections import deque
from types import NoneType
from typing import Optional, Literal
from functools import partial
import asyncio
from aiogram import Router, types, filters, html, F
from aiogram.fsm.context import FSMContext
from root.keyboards.FAQ.FAQ_keyboard import Inline_FAQ, faq_list, FAQ_CD, FAQGroup
from root.utils.execute import execute, awaitable_reply_markup
from root.config.config import privileged_users, faq_group_list, PrivilegedUser, perem_iteration
from ...keyboards import close, main_menu

router = Router()


async def FAQ(message: types.Message | types.CallbackQuery, callback_data: FAQ_CD = None, **kwargs):
    text = f"{html.bold('Выберите интересующий Вас вопрос из списка ЧаВо/ЧЗВ/FAQ')}"
    if not callback_data:
        callback_data = {'depth'}
        if privileged_users[message.from_user.id]['update_faq'] or privileged_users[message.from_user.id]['super_user']:  # O(1) т.к. ищется хэш в set через хеш-таблицу
            callback_data.add('user')
    await execute(message, text, reply_markup=Inline_FAQ.get_faq, callback_data=callback_data,
                  advanced_args={"user": message.from_user, "the_main": True})


async def cb_FAQ(call: types.CallbackQuery, callback_data: FAQ_CD):
    user_privileges = privileged_users.get(call.from_user.id)
    is_superusers = user_privileges and (user_privileges.get('update_faq') or
                                         user_privileges.get('super_user'))
    if is_superusers and callback_data.depth == 0 and callback_data.is_privileged:
        await call.message.edit_text(f"FAQ", reply_markup=await Inline_FAQ.admin_table(depth=0, user=call.from_user))
    elif callback_data.depth == 0:
        task = asyncio.create_task(FAQ(message=call, callback_data=callback_data))
        await task
    else:
        await call.message.edit_text(
            faq_list[callback_data.id]['answer'],
            reply_markup=await Inline_FAQ.back_to_FAQ(FAQ_CD, callback_data.depth, the_main=callback_data.the_main))
    await call.answer()


async def FAQ_Group(message: types.CallbackQuery, state: FSMContext, callback_data: FAQ_CD | FAQGroup = None, **kwargs):
    text: str = kwargs.get('text')
    group_list = kwargs.get('group_list') if kwargs.get('group_list') else []

    try:
        await message.message.edit_text(text, reply_markup=await Inline_FAQ.get_faq_group(
            depth=callback_data.depth, group_list=group_list, mov=callback_data.mov, other_group=callback_data.group,
            admin_panel=False, tmp_perem=kwargs.get('tmp_perem'), cancel=kwargs.get('cancel'),
            in_mov=kwargs.get('is_admin')
        ))
    except: pass


async def faq_group(com: types.CallbackQuery | types.Message, state, callback_data: FAQGroup = None, **kwargs):
    state: FSMContext
    text = f"{html.bold('Выберите интересующий Вас вопрос из списка ЧаВо/ЧЗВ/FAQ')}"
    callback_func = Inline_FAQ.group_faq_table if isinstance(callback_data, FAQGroup) else Inline_FAQ.admin_table
    mov = callback_data.mov if callback_data and callback_data.mov is True else bool(kwargs.get('mov'))
    kwargs.update(mov=mov)

    match callback_data.model_dump() if callback_data else {'depth': 0}:
        case {'depth': depth}:
            if depth < 0:
                return await com.message.edit_text('.', reply_markup=main_menu())
            await get_panel(com, callback_data, text, callback_func, state, **kwargs)
        case _: await com.message.edit_text("Закрыть", reply_markup=close("закрыть"))


async def get_panel(com: types.CallbackQuery | types.Message, callback_data, text, callback_generate_func, state, **kwargs):
    user: PrivilegedUser = privileged_users.get(com.from_user.id)
    is_admin: bool = bool(user) and (user['super_user'] or user['update_faq']) and not kwargs.get('mov')
    is_admin_panel = is_admin and not callback_data.admin_panel
    callback_data = callback_data if callback_data else {'depth'}

    group_list = await get_group_list_and_last_group(callback_data, state, is_admin, kwargs.get('param'))

    group_list = await try_it('faq_group_list', group_list, callback_data, state, is_admin)

    if is_admin_panel:
        if isinstance(callback_data, set): callback_data.add('user')
        return await execute(com, text, callback_data=callback_data, reply_markup=callback_generate_func, advanced_args={'depth': 0, 'user': com.from_user, 'group': callback_data.group,
                                                                                                                         'groups': len(group_list), 'mov': bool(kwargs.get('mov'))})

    text = group_list['answer'] if (group_list != faq_group_list) and isinstance(group_list, dict) else text

    await FAQ_Group(message=com, text=text, callback_data=callback_data, group_list=group_list, state=state,
                    prev_group=group_list, is_admin=is_admin, **kwargs)


async def try_it(raw_group_list, group_list: str, callback_data, state, is_admin) -> dict:
    if len(group_list) == 0 and callback_data.depth > 1 and not callback_data.back: callback_data.depth = 0
    if callback_data.depth == 0: await state.update_data(check_faq=False)
    try:
        # print(raw_group_list, group_list)
        result = eval(f'{raw_group_list}{group_list}')
        if result == faq_group_list: reset_depth(callback_data, is_admin)
        return result
    except KeyError as err:
        print(f"{err=}")
        await state.clear()
        reset_depth(callback_data, is_admin)
        return eval(raw_group_list)


def reset_depth(callback_data, is_admin):
    if is_admin:
        callback_data.depth = 0 if not callback_data.admin_panel else 1
    else:
        callback_data.depth = 0


async def get_group_list_and_last_group(callback_data, state, is_admin, param):
    context = await state.get_data()
    check_faq = bool(context.get('check_faq'))
    gl = group_list = context['group_list'] if context.get('group_list') else []
    gl_existed = bool(len(gl))

    name_group = context.get('name_group')

    if name_group and param:
        return context['str_group_list']

    if not isinstance(callback_data.group, NoneType):
        if gl_existed and callback_data.group != gl[-1]:
            gl.append(callback_data.group)
        elif not gl_existed and not callback_data.back:
            gl.append(callback_data.group)

    if group_list:
        group_back(callback_data, group_list, is_admin)

        gl = group_list[:]

        group_list = [f"[\'{group}\']" for group in group_list]
        group_list = ''.join(group_list)

    if not group_list:
        group_list = ''

    if len(gl) == 0 or callback_data.depth == 0:
        check_faq = False
        gl.clear()
        group_list = ''

    if hasattr(gl, '__len__') and callback_data.group is not None and not check_faq and not callback_data.back:
        group_list = f"[\'{callback_data.group}\']"
        check_faq = True

    # print(context.get('name_group'))
    await state.update_data(group_list=gl, check_faq=check_faq, str_group_list=group_list,
                            name_group=context.get('name_group'), tmp_perem=False)

    return group_list


def group_back(callback_data, group_list: list, is_admin: bool) -> bool:
    if callback_data.back and ((is_admin and callback_data.admin_panel) or not is_admin):
        group_list.pop()
        return True
    return False


router.callback_query.register(faq_group, FAQGroup.filter())
router.callback_query.register(cb_FAQ, FAQ_CD.filter(F.for_delete.is_(False) | F.for_edit.is_(False)))
router.message.register(faq_group, filters.Command('faq'))
