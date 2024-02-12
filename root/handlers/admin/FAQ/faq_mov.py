import asyncio
import json
from typing import OrderedDict
from copy import deepcopy

from aiogram import filters, Router, F
from aiogram.fsm.context import FSMContext

from root.config.config import RedisDict
from root.handlers.client.faq import faq_group
from root.keyboards.FAQ.FAQ_keyboard import FAQGroup, PseudoCB, Inline_FAQ
from root.keyboards.button_sorter import ButtonSorter
from root.config import faq_group_list, pool

router = Router()


async def get_text(call, callback_data, state, **kwargs):
    await func(call, callback_data, state, mov=True, text='Выберите место для переноса')


async def mov_cancel(call, callback_data, state, **kwargs):
    context = await state.get_data()
    temp_group_list = RedisDict('temp_group_list')
    faq_group_list.update(temp_group_list)
    temp_group_list.clear()
    callback_data.depth = context['real_depth'] if context.get('real_depth') else 0
    real_group_list = context['real_group_list']
    str_group_list = [f'[\'{group}\']' for group in real_group_list]
    str_group_list = ''.join(str_group_list)
    context.update(param=None, group=None, name_group=None, real_str_group_list=None, real_depth=None,
                   str_group_list=str_group_list, real_group_list=None,
                   group_list=real_group_list)
    callback_data.group = real_group_list[-1] if real_group_list else ''
    await state.update_data(**context)
    await asyncio.sleep(1.01)
    kwargs.update(call=call, callback_data=callback_data, state=state, mov=callback_data.mov, text='')
    await func(**kwargs)


async def mov_done(call, callback_data, state, **kwargs):
    context = await state.get_data()
    str_group_list = context['str_group_list']
    group_list: dict = eval(f"faq_group_list{str_group_list}")
    group_list.update({context['name_group']: context['group']})
    faq_group_list.update(faq_group_list)
    await state.update_data(param=None, group=None, name_group=None, real_str_group_list=None, real_depth=None,
                            real_group_list=None)
    context = await state.get_data()
    callback_data.mov = False
    callback_data.done = False
    RedisDict('temp_group_list').clear()
    kwargs.update(com=call, callback_data=callback_data, state=state)
    await faq_group(**kwargs)


async def func(call, callback_data, state, mov, text, done = False, **kwargs):
    if callback_data.cancel:
        callback_data.mov = False
        callback_data.cancel = False
        return await faq_group(call, state, callback_data, cancel=True)

    context = await state.get_data()
    str_group_list = context['str_group_list'] if context.get('str_group_list') else ''
    group = context.get('group')
    name_group = context.get('name_group')
    group_list = context.get('group_list')

    param = False
    if not name_group and not group and not callback_data.back:
        name_group = callback_data.group
        temp_group_list = RedisDict('temp_group_list')
        temp_group_list.update(faq_group_list)
        group_list = context.get('group_list')
        try:
            group_list.remove(name_group)
        except: pass
        print(group_list)
        str_group_list = group_list if group_list else ''
        str_group_list = [f'[\'{group}\']' for group in str_group_list]
        str_group_list = ''.join(str_group_list)
        group = eval(f'faq_group_list{str_group_list}.pop(name_group)')
        faq_group_list.update(faq_group_list)
        context.update(group=group)
        callback_data.cancel = False
        param = True

    if group is None and callback_data.back:
        callback_data.mov = False
        callback_data.cancel = False
        return await mov_cancel(call=call, state=state, callback_data=callback_data, cancel=True, param=param)

    context.update(str_group_list=str_group_list, name_group=name_group, group_list=group_list)
    await state.update_data(**context)

    await asyncio.sleep(0.01)
    kwargs.update(com=call, callback_data=callback_data, state=state, param=param)
    await faq_group(**kwargs)


async def puk(call, state: FSMContext, callback_data, **kwargs):
    context = await state.get_data()
    await state.update_data(real_str_group_list=context['str_group_list'], real_depth=callback_data.depth,
                            real_group_list=context['group_list'], tmp_perem=True)

    await faq_group(com=call, state=state, callback_data=callback_data, mov=callback_data.mov, tmp_perem=True, **kwargs)


router.callback_query.register(mov_done, FAQGroup.filter(F.mov.is_(True) & F.done.is_(True)))
router.callback_query.register(mov_cancel, FAQGroup.filter(F.mov.is_(True) & F.cancel.is_(True)))
router.callback_query.register(puk, FAQGroup.filter(F.mov.is_(True) & F.admin_panel.is_(True)))
router.callback_query.register(get_text, FAQGroup.filter(F.mov.is_(True)))
