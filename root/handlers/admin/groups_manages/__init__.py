from .hub import *
from .add_group import *
from .delete_group import *
from .editable_groups import *


async def group_redistributor(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext):
    depth_func = {
        0: manage_groups,
        1: select_choice_group_or_subgroup_edit if callback_data.edit else select_delete_group,
        2: edit_groups if callback_data.edit else delete_group,
        3: edit_group_permission if callback_data.permissions_editable else choice_which_group_to_obey if
        callback_data.subordinate_editable else final_delete_group
    }

    await depth_func[callback_data.depth](
        call,
        callback_data=callback_data,
        state=state,
    )
