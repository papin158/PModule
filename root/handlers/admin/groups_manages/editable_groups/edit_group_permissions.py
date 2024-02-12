from aiogram import types, html
from aiogram.fsm.context import FSMContext

from root.keyboards.super_users import GroupEditable, Inline
from root.config import Group as config_group, groups
from root.utils.databases.postgresql import Groups


async def edit_group_permission(call: types.CallbackQuery, callback_data: GroupEditable, state: FSMContext):
    """
    Изменяются разрешения для каждой отдельной группы.
    :param call:
    :param callback_data:
    :param state:
    :return: ничего.
    """
    context = await state.get_data()
    temp_groups = context.get('temp_groups')
    list_temp_groups: list[str] = context.get('list_temp_groups')
    editable_group = list_temp_groups[callback_data.index_editable_group]

    if isinstance(callback_data.permission_name, int):
        temp_groups[editable_group][f"{list(temp_groups[editable_group].keys())[callback_data.permission_name]}"] = \
            not callback_data.permission_state

    await call.message.edit_text(f"Изменяются права группы \"{html.bold(editable_group)}\"",
                                 reply_markup=await Inline.group_permission_edit(
                                     depth=callback_data.depth, editable_group=editable_group,
                                     edit=callback_data.edit, temp_groups=temp_groups,
                                     index_editable_group=callback_data.index_editable_group,
                                     delete=callback_data.delete, user_id=call.from_user.id
                                 ))

    await state.update_data(temp_groups=temp_groups, editable_group=editable_group)


async def finish_editing_group_permissions(context: dict):
    editable_group = context.get('editable_group')
    temp_groups: dict[..., config_group] = context.get('temp_groups')
    await Groups().add(editable_group,
                       add_or_delete_group=temp_groups[editable_group]['add_or_delete_group'],
                       update_user_group=temp_groups[editable_group]['update_user_group'],
                       update_permissions_subgroup=temp_groups[editable_group]['update_permissions_subgroup'],
                       update_faq=temp_groups[editable_group]['update_faq'])
    for group in temp_groups:
        groups[group] = temp_groups[group]
