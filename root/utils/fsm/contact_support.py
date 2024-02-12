from aiogram.fsm.state import StatesGroup, State


class ContactSupport(StatesGroup):
    WAIT = State()
    WORK = State()

