from aiogram.fsm.state import StatesGroup, State


class AddNewGroup(StatesGroup):
    NAME_NEW_GROUP = State()
    FIND_USER = State()
