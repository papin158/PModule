import numpy as np, math
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from collections import namedtuple, deque

__all__ = [
    'exe',
    'Iteration_CallbackData',
    'all_keyboards_for_main_manu',
    'main_keyboard',
    'MainMenu'
]

exe = '''size = buttons.size if isinstance(buttons, np.ndarray) else len(buttons)
if size: 
    division_result = math.floor(size / len_rows)
    remainder_of_division = size % len_rows
    rows = np.full(shape=division_result, fill_value=len_rows, dtype=object)
else:
    division_result = 0
    remainder_of_division = 0
    rows = []

if remainder_of_division: rows = np.append(rows, [remainder_of_division, *[1] * custom_b])
builder.adjust(*rows)
'''
exe = compile(exe, '', 'exec', optimize=1)

Iteration_CallbackData = namedtuple("CallbackData", "description callback")
all_keyboards_for_main_manu = deque()


async def main_keyboard():
    rows: int = 3
    builder = InlineKeyboardBuilder()
    [builder.button(text=j.description, callback_data=j.callback) for j in all_keyboards_for_main_manu]
    builder.button(text="Закрыть", callback_data=MainMenu(cancel=True))
    exec(exe, {'builder': builder, 'buttons': all_keyboards_for_main_manu, 'len_rows': rows,
               'math': math, 'np': np, 'custom_b': 1})

    return builder.as_markup()


class MainMenu(CallbackData, prefix='main_menu'):
    main: bool = False
    cancel: bool = False
