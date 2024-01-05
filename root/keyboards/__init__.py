import numpy as np, math, aiogram, typing
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from collections import namedtuple, deque


__all__ = [
    'exe',
    'Iteration_CallbackData',
    'all_keyboards_for_main_manu',
    'main_keyboard',
    'create_order_button',
    'MainMenu'
]

exe = '''size = buttons.size if isinstance(buttons, np.ndarray) else buttons if isinstance(buttons, int) else len(buttons)
if size: 
    division_result = math.floor(size / len_rows)
    remainder_of_division = size % len_rows
    rows = np.full(shape=division_result, fill_value=len_rows, dtype=object)
else:
    division_result = 0
    remainder_of_division = 0
    rows = []

if remainder_of_division: rows = np.append(rows, [remainder_of_division, *[1] * custom_b])
builder.adjust(*rows, *[1] * custom_b)
'''
exe = compile(exe, '', 'exec', optimize=1)


def create_order_button(builder: InlineKeyboardBuilder, buttons: np.ndarray | typing.Iterable | int,
                        len_rows: int = 2, custom_buttons: int = 1) -> None:
    """
    Сортирует кнопки, чтобы те не ломали порядок.
    :param builder: Билдер кнопок.
    :param buttons: Передать сами кнопки.
    :param len_rows: Количество столбцов.
    :param custom_buttons: Количество кнопок, которые нужно отделить по одной от остальных.
    Будут перенесены только последние переданные кнопки в buttons.
    :return: Ничего не возвращает.
    """
    exec(exe, {'builder': builder, 'buttons': buttons, 'len_rows': len_rows,
               'math': math, 'np': np, 'custom_b': custom_buttons})


Iteration_CallbackData = namedtuple("CallbackData", "description callback")
all_keyboards_for_main_manu = deque()


async def main_keyboard(suser_callback=None):
    rows: int = 2
    builder = InlineKeyboardBuilder()
    [builder.button(text=j.description, callback_data=j.callback) for j in all_keyboards_for_main_manu]
    if suser_callback:
        builder.button(text="Панель администратора", callback_data=suser_callback)
    builder.button(text="Закрыть", callback_data=MainMenu(cancel=True))
    exec(exe, {'builder': builder, 'buttons': all_keyboards_for_main_manu, 'len_rows': rows,
               'math': math, 'np': np, 'custom_b': 1})

    return builder.as_markup()


class MainMenu(CallbackData, prefix='main_menu'):
    main: bool = False
    cancel: bool = False
