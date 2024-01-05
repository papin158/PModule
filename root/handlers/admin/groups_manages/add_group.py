from aiogram import types, Bot, html
from aiogram.fsm.context import FSMContext

from root.config import groups, privileged_users
from root.config import update_privileged_users as update_groups
from root.keyboards.FAQ.admin.fsm_state import default_cancel, fsm_final
from root.keyboards.super_users.super_users import SuperUserMenu, Inline
from root.utils.fsm.admin_menu import AddNewGroup


async def add_group(call: types.CallbackQuery, callback_data: SuperUserMenu, state: FSMContext, **kwargs):
    """
    Создание новой группы
    :return:
    """
    message_for_edit = await call.message.edit_text("Придумай и напиши название группы", reply_markup=None)
    del_mes = await call.message.answer("_", reply_markup=await default_cancel())
    await state.update_data(message_for_edit=message_for_edit.model_dump_json(), del_mes=del_mes.model_dump_json(),
                            depth=callback_data.depth)
    await state.set_state(AddNewGroup.NAME_NEW_GROUP)


async def send_new_group(message: types.Message, state: FSMContext, bot: Bot, **kwargs):
    context = await state.get_data()
    text = message.text
    await message.delete()
    mes = types.Message.model_validate_json(context['message_for_edit']).as_(bot)
    del message

    if text not in groups:
        await mes.edit_text(
            f"Группа будет названа {html.pre(text)}\nЕсли всё устраивает нажмите \"Готово\"",
            reply_markup=await Inline.finish(depth=context['depth'], add_group=True, create=True))
        await state.update_data(group_name=text)
        return

    await mes.edit_text(
        f"Уже существует группа с названием {html.pre(text)}\nПридумайте другое название.",
        reply_markup=await Inline.close()
    )


@fsm_final(text="Группа создана")  # , del_mes='del_mes', message_for_edit = 'message_for_edit')
async def create_group(call, state: FSMContext, context: dict,  *args, **kwargs):
    """
    Если пользователь не супер-пользователь, тогда создаваемая им группа будет приписана всем его родительским группам,
    Иначе группа будет добавлена без родителей.
    """
    if not privileged_users[call.from_user.id]['super_user']:
        higher_user_groups = set(privileged_users[call.from_user.id]['user_groups']) - \
                             set(privileged_users[call.from_user.id]['user_subordinate_groups'])
    else: higher_user_groups = None

    await update_groups(new_group=context['group_name'], higher_user_groups=higher_user_groups)
