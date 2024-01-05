import asyncio

from aiogram import types, html
from aiogram.fsm.context import FSMContext

from root.config import update_privileged_users as update_groups, privileged_users, groups
from .hub import manage_groups
from root.keyboards.super_users.super_users import SuperUserMenu, Inline
from root.utils.databases.postgresql import Groups


async def select_delete_group(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext):
    sub_groups = list(sorted(privileged_users[call.from_user.id]['user_subordinate_groups']))
    await state.update_data(sub_groups=sub_groups)
    await call.message.edit_text("Выберите группу", reply_markup=await Inline.list_groups_for_edit(
        depth=callback_data.depth,  sub_groups=sub_groups,
        permissions_editable=False, subordinate_editable=False, edit=False, delete=True
    ))


async def delete_group(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext):
    context = await state.get_data()
    sub_groups = context['sub_groups']
    deleted_group = context['deleted_group'] if context.get('deleted_group') else sub_groups[callback_data.index_editable_group]
    await call.message.edit_text(
        f"Удалить группу: \"{html.bold(deleted_group)}\"",
        reply_markup=await Inline.confirm_to_delete(
            depth=callback_data.depth
        ))
    await state.update_data(deleted_group=deleted_group)


async def final_delete_group(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext):
    context = await state.get_data()
    mes = await call.message.answer(f"Группа \"{html.bold(context['deleted_group'])}\" удалена")
    await state.clear()
    callback_data.delete = False
    callback_data.depth = 0
    groups.pop(context['deleted_group'])
    await manage_groups(call=call, state=state, callback_data=callback_data)
    sql_groups = Groups()
    await sql_groups.del_(context['deleted_group'])
    await update_groups()
    await asyncio.sleep(1.76)
    await mes.delete()
