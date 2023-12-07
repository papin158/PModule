from aiogram.fsm.state import StatesGroup, State


class FAQ(StatesGroup):
    GET_QUESTION = State()  # Получаем вопрос для записи
    ONLY_QUESTION = State()
    GET_ANSWER = State()  # Получаем ответ на вопрос
    ONLY_ANSWER = State()
