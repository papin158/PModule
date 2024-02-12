import typing
from copy import deepcopy

from aiogram import types, html
from aiogram.fsm.context import FSMContext

from root.config import Group as config_group, privileged_users
from root.keyboards.super_users import GroupEditable, Inline
from root.utils.databases.postgresql import SGroups


async def choice_which_group_to_obey(call: types.CallbackQuery, callback_data: GroupEditable, state: FSMContext) \
        -> None:
    """
    Основная структура, которая отвечает за комплекс мер по изменению субординации. Именно она будет вызываться
    пользователем при изменении субординации.
    :param call: Коллбэк telegram который срабатывает при нажатии на кнопки.
    :param callback_data: Данные, которые записываются при каждом нажатии на кнопку.
    :param state: Машинное состояние, или временный кэш данных.
    """
    context = await state.get_data()
    iter = int(context.get('iter')) if context.get('iter') else 0
    temp_groups: dict[..., config_group] = context.get('temp_groups')
    list_temp_groups: list[str] = context.get('list_temp_groups')
    subgroups = context.get('subgroups')
    temp_subordinate = deepcopy(temp_groups)
    editable_group = list_temp_groups[callback_data.index_editable_group]
    selected_groups = set(context.get('selected_groups')) if isinstance(context.get('selected_groups'), list) else set(
        temp_subordinate[editable_group]['subordinate_groups'])
    unsorted_selected_groups = list(dict.fromkeys(context.get('unsorted_selected_groups'))) if context.get('unsorted_selected_groups') else list()

    temp_subordinate[editable_group]['subordinate_groups'].clear()

    if not isinstance(subgroups, list):
        subgroups: list = create_subgroups(call=call, editable_group=editable_group, temp_groups=temp_groups)

    selected_groups = update_subgroups(callback_data=callback_data, selected_groups=selected_groups, subgroups=subgroups)

    unsorted_selected_groups = await what_subgroups_changed(callback_data=callback_data, selected_groups=unsorted_selected_groups, subgroups=subgroups)

    temp_subordinate[editable_group]['subordinate_groups'].extend(selected_groups)
    text = f"\n   · ".join(unsorted_selected_groups)
    text = f'{"   · " if text else ""}' + text

    await call.message.edit_text(f"Группы, которые будут изменены у {editable_group}:\n"
                                 f"{text}\n"
                                 f"Не забывайте, что нельзя наследнику наследовать родителя.",
                                 reply_markup=await Inline.choose_group(
                                     depth=callback_data.depth,
                                     editable_group=editable_group,
                                     temp_groups=temp_subordinate[editable_group]['subordinate_groups'],
                                     sub_groups=subgroups,
                                     index_editable_group=callback_data.index_editable_group,
                                     menu=GroupEditable
                                 ))

    await state.update_data(iter=iter+1, temp_groups=temp_groups, selected_groups=selected_groups, subgroups=subgroups,
                            editable_group=editable_group, unsorted_selected_groups=unsorted_selected_groups)
    await call.answer()


def create_subgroups(call: types.CallbackQuery, editable_group: str,
                     temp_groups: dict[..., config_group]) -> list:
    """
    Назначение какой-либо группе подчинённой.
    :param call: Нужен для получения id пользователя, мне так захотелось.
    :param editable_group: Группа, которой будут подчинять выбранные пользователем группы.
    :param temp_groups: Временная переменная, которая будет учитывать изменения в субординациях.
    :return: Отсортированный список групп.
    """
    subgroups = set(privileged_users[call.from_user.id]['user_subordinate_groups'].copy())
    subgroups.discard(editable_group)
    delete_groups = set()
    for group in subgroups:
        if editable_group in temp_groups[group]['subordinate_groups']: delete_groups.add(group)
    subgroups = subgroups - delete_groups
    return list(sorted(subgroups))


def update_subgroups(callback_data: GroupEditable, selected_groups: set, subgroups: list
                     ) -> typing.Optional[typing.Iterable]:
    """
    Список, который будет показывать пользователю, какие группы в каком состоянии.
    :param callback_data: Данные из системы обратных связей aiogram, чтобы получать доступ к изменённым структурам.
    :param selected_groups: Группы, которые пользователь, имеющий права на редактирование субординации, изменил.
    :param subgroups: Список групп, которые доступны для изменения пользователю.
    :return: Неотсортированный список всех групп, указывающие, какое у них состояние в данный момент.
    """
    if callback_data.subordinate_state:
        selected_groups.add(subgroups[callback_data.subordinate_index])
    elif callback_data.subordinate_state is False:
        selected_groups.discard(subgroups[callback_data.subordinate_index])
    return list(selected_groups)


async def what_subgroups_changed(callback_data: GroupEditable, selected_groups: list, subgroups: list
                                 ) -> typing.Optional[typing.Iterable]:
    """
    Проверка данных на ввод, если пользователь меняет какую-то группу, она должна быть в списке, чтобы ничего не
    терялось.
    :param callback_data: Данные из системы обратных связей aiogram, чтобы получать доступ к изменённым структурам.
    :param selected_groups: Группы, которые пользователь, имеющий права на редактирование субординации, изменил.
    :param subgroups: Список групп, которые доступны для изменения пользователю.
    :return: Неотсортированный список всех групп, которые будут изменены пользователем.
    """
    if isinstance(callback_data.subordinate_index, int):
        if not subgroups[callback_data.subordinate_index] in selected_groups:
            selected_groups.append(subgroups[callback_data.subordinate_index])
        else:
            selected_groups.remove(subgroups[callback_data.subordinate_index])
    return selected_groups


async def edit_subgroups(call: types.CallbackQuery, **_):
    await call.message.edit_text("Выберите группу, которой нужно настроить иерархию", reply_markup=None)


async def finish_editing_group_subordinates(context: dict) -> None:
    """
    Получение данных машины состояний, и в соответствии с ними, менять значения в базе данных, которые отвечают
    за субординацию групп.
    :param context: Данные машины состояний aiogram.
    """
    editable_group = context.get('editable_group')
    temp_groups: dict[..., config_group] = context.get('temp_groups')
    selected_groups = set(context.get('selected_groups'))
    default_subordinate_groups = set(temp_groups[editable_group]['subordinate_groups'])

    remove_inheritance = default_subordinate_groups - selected_groups
    add_inheritance = selected_groups - default_subordinate_groups
    sgroups = SGroups()

    if remove_inheritance:
        for group in remove_inheritance:
            await sgroups.del_one(editable_group, group)
    if add_inheritance:
        for group in add_inheritance:
            await sgroups.add_one(editable_group, group)
