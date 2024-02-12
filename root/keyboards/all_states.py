from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

__all__ = [
    'close',
    'main_menu'
]


def b_close(text) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data='close_state')


def close(text):
    markup = InlineKeyboardMarkup(inline_keyboard=[[b_close(text)]])
    return markup


def get_menu(text) -> InlineKeyboardButton:
    from root.keyboards import MainMenu
    return InlineKeyboardButton(text=text, callback_data=MainMenu(main=True).pack())


def main_menu(text='В меню'):
    markup = InlineKeyboardMarkup(inline_keyboard=[[get_menu(text)]])
    return markup
