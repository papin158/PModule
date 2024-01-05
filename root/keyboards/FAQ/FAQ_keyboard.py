import numpy as np, math
from typing import Optional
from root.keyboards import exe, MainMenu, all_keyboards_for_main_manu, Iteration_CallbackData
from root.config.config import faq_list, privileged_users
from .admin import fsm_state
from aiogram.filters.callback_data import CallbackData
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

# desc = np.array([
#     [
#         "Как вступить в ПМ?",
#         'Зачем люди приходят в ПМ?',
#         "Что нужно уметь, чтобы вступить в ПМ?",
#         'Сколько проектов в вашей копилке?',
#         'Мне страшно начать.',
#         'К кому можно обратиться по вступлению в проекты?',
#
#     ],
#     [
#         "Главное - твоё желание. Если ты хочешь начать работу в ПМ, напиши нашему секретарю. ",
#         'Студенты приходят по разным причинам, среди которых:\n1. Интерес к работе.\n2. Личное развитие.\n3. Социальное влияние',
#         "Топ-3 компетенции для Проектёра:\n1. Коммуникабельность\n2. Открытость\n3. Критическое мышление",
#         'У нас 3 завершенных проекта, 1 проект - активный, а также несколько проектов планируются в работу.',
#         'Боитесь, что не справитесь? Не знаете что делать?\nМы все с чего-то начинаем. Не бойтесь пробовать что-то новое. Никто вас ни за что не осудит:)',
#         'Вы можете обратиться к главе ПМ - Дейчман Анне или к заместителям главы ПМ - Шлячковой Катерине и Бижановой Кристине'
#     ]
# ])


class FAQ_CD(CallbackData, prefix='faq'):
    __slots__ = ()
    id: Optional[int] = None
    depth: int
    for_delete: bool = False
    for_edit: bool = False
    the_main: bool = False
    get_for_privileged_user: bool = False
    is_privileged: bool = True


class Admin_FAQ_CD(CallbackData, prefix='amd_faq'):
    __slots__ = ()
    admin: bool = False
    # depth: Optional[int] = None


class Inline_FAQ:
    __slots__ = ()

    @classmethod
    async def get_faq(cls, depth, for_delete: bool = False, the_main: bool = False, for_edit: bool = False,
                      is_privileged: bool = False, user: types.Union[types.User, bool] = None) -> InlineKeyboardMarkup:
        """
        Генерируется таблица в соответствии с вложенностью, а так же, с указанием, для удаления она, или является ли
        она основной, если таблица является основной, то пользователю не будет сформирована кнопка для возврата в
        Main Menu.
        :param user: Пользователь.
        :param is_privileged: Имеет ли пользователь права.
        :param for_edit: Нужно ли редактировать таблицу.
        :param depth: Уровень вложенности.
        :param for_delete: Сформирована ли таблица с целью удаления строк в ней.
        :param the_main: Является ли таблица основной, если да, то возврата в Main Menu не будет.
        :return: Возвращает клавиатуру, привязываемую к сообщению.
        """
        builder = InlineKeyboardBuilder()   # Присваиваем "создатель" для таблицы
        len_rows: int = 1   # Указываем количество колонок
        custom_b: int = 1   # Указываем количество кнопок, которые должны быть в 1 строку

        if faq_list:  # Если описание не пустое, значит делаем перебор всех значений, и добавление их в таблицу
            for n, but_desc in enumerate(faq_list):
                builder.button(text=but_desc['question'],
                               callback_data=FAQ_CD(id=n, depth=depth+1, for_delete=for_delete, for_edit=for_edit,
                                                    is_privileged=is_privileged, the_main=the_main))

        text = "Назад"  # Стандартный текст кнопки назад
        puser = privileged_users.get(user.id)

        if user and (isinstance(user, types.User) and puser and
                     (puser.get('update_faq') or puser.get('super_user'))) or isinstance(user, bool):
            callback_data = Admin_FAQ_CD(admin=True)
        elif not (for_delete or is_privileged or for_edit) or depth == 0:
            callback_data = MainMenu(main=True)

        else:
            callback_data = FAQ_CD(depth=0 if depth - 1 < 0 else depth - 1, for_delete=for_delete, for_edit=for_edit,
                                   is_privileged=is_privileged, the_main=the_main)

        if the_main:    # Если таблица является основной, тогда вместо кнопки "Назад" будет кнопка "Закрыть"
            callback_data = MainMenu(cancel=True)
            text = "Закрыть"

        builder.button(text=text, callback_data=callback_data)  # Здесь просто добавляется сформированная кнопка

        buttons = len(faq_list)  # Считаем количество кнопок

        async def resize(length_rows):  # Функция уменьшает количество колонок, если количество кнопок не может
            if buttons < length_rows * 2:  # составить даже две строки
                return resize(length_rows - 1)
            return length_rows

        if len_rows > 1:    # делает проверку, займут ли кнопки две строчки, в каждой колонке
            len_rows = await resize(length_rows=len_rows)

        # Пересчитывает, а так же строит таблицу
        exec(exe, {'builder': builder, 'buttons': faq_list, 'len_rows': len_rows,
                   'math': math, 'np': np, 'custom_b': custom_b})

        return builder.as_markup()  # Возвращает таблицу (клавиатуру)

    @classmethod
    async def back_to_FAQ(cls, callback_data, depth, the_main: bool = False) -> InlineKeyboardMarkup:
        """
        Если пользователь получил данные по таблице и хочет получить больше вопросов, без необходимости заново
        прописывать команды.
        :param callback_data: Какая callback_data должна вызываться.
        :param the_main: Является ли таблица, в которую возвращаемся основной.
        :param depth: Глубина меню (многоуровневого).
        :return: Возвращает сформированную клавиатуру (таблицу).
        """
        builder = InlineKeyboardBuilder()

        builder.button(text='Ещё вопросы', callback_data=callback_data(id=-1, depth=0, the_main=the_main,
                                                                       is_privileged=False))
        builder.button(text='Закрыть', callback_data=MainMenu(cancel=True))

        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    async def confirm_to_delete_faq(cls, id: int | None, depth, empty: bool = False) -> InlineKeyboardMarkup:
        """
        Подтверждение того, готов ли администратор удалить вопрос из FAQ.
        :param id: Идентификатор вопроса.
        :param empty: Пустой ли список
        :param depth: Глубина меню (многоуровневого).
        :return: Возвращает сформированную клавиатуру (таблицу).
        """
        builder = InlineKeyboardBuilder()

        if not empty or id is None: builder.button(text="Готово", callback_data=FAQ_CD(id=id, depth=depth+1, for_delete=True))
        builder.button(text='Назад', callback_data=Admin_FAQ_CD(admin=True))

        return builder.as_markup()

    @classmethod
    async def FAQ_edit(cls, depth) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.button(text='Изменить название', callback_data=fsm_state.FAQ_Edit_CB(depth=depth+1, title_only=True))
        builder.button(text='Изменить описание', callback_data=fsm_state.FAQ_Edit_CB(depth=depth+1, answer_only=True))
        builder.button(text="Назад", callback_data=FAQ_CD(id=0, depth=depth-1, is_privileged=False, for_edit=True))

        builder.adjust(2, 1)

        return builder.as_markup()

    @classmethod
    async def admin_table(cls, depth, user: types.User) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.button(text="список FAQ", callback_data=FAQ_CD(id=0, depth=depth, is_privileged=False))
        builder.button(text="создать FAQ", callback_data=fsm_state.FAQ_Edit_CB(depth=0))
        builder.button(text="изменить FAQ", callback_data=FAQ_CD(id=0, depth=depth, for_edit=True, is_privileged=False))
        builder.button(text="удалить FAQ", callback_data=FAQ_CD(id=0, depth=depth, for_delete=True, is_privileged=False))
        builder.button(text="Назад FAQ", callback_data=MainMenu(main=True))

        builder.adjust(2)

        return builder.as_markup()


callback = FAQ_CD(id=0, depth=0)


all_keyboards_for_main_manu.append(
    Iteration_CallbackData(description="ЧаВо/FAQ", callback=FAQ_CD(id=0, depth=0))
)

