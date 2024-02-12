from .edit_subordinate import *
from .edit_group_permissions import *
from root.config import update_privileged_users


async def edit_groups(call: types.CallbackQuery, callback_data: GroupEditable, state: FSMContext, **_):
    user = privileged_users.get(call.from_user.id)
    data = await state.get_data()
    temp_groups: dict[..., config_group] = {}

    if callback_data.done:
        if callback_data.permissions_editable: await finish_editing_group_permissions(data)
        elif callback_data.subordinate_editable: await finish_editing_group_subordinates(data)
        await update_privileged_users()
        await state.clear()

    if not user['super_user']:
        for subgroup in privileged_users[call.from_user.id]['user_subordinate_groups']:
            if subgroup in groups:
                temp_groups[subgroup] = deepcopy(groups[subgroup])
        temp_groups: dict[..., config_group] = dict(sorted(temp_groups.items()))
    else: temp_groups: dict[..., config_group] = deepcopy(groups)
    list_temp_groups = list(temp_groups.keys())

    await call.message.edit_text("text", reply_markup=await Inline.list_groups_for_edit(
        depth=callback_data.depth, sub_groups=temp_groups,
        permissions_editable=callback_data.permissions_editable,
        subordinate_editable=callback_data.subordinate_editable))
    await call.answer()
    await state.update_data(temp_groups=temp_groups, subgroups=None, selected_groups=None, iter=0,
                            list_temp_groups=list_temp_groups, unsorted_selected_groups=None)


async def select_choice_group_or_subgroup_edit(call: types.CallbackQuery, callback_data: GroupEditable,
                                               state: FSMContext):
    await call.message.edit_text("Выберите, что следует изменить",
                                 reply_markup=await Inline.group_select_for_edit(depth=callback_data.depth))
