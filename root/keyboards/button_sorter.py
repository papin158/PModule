import enum
import math
from collections import deque
from dataclasses import dataclass
from typing import NamedTuple, TypeVar, Collection

from aiogram.utils.keyboard import InlineKeyboardButton

_T = TypeVar("_T")


class Position(enum.Enum):
    before_main_buttons = 0
    after_main_buttons = 1


@dataclass
class CustomPosition:
    buttons: Collection[InlineKeyboardButton]
    position: Position
    rows: int | None = None


class ButtonSorter:
    """Сортирует и добавляет кнопки в правильном порядке"""
    __slots__ = 'builder', 'rows', '__custom_buttons_positions',  '__buttons'

    __custom_buttons_positions: deque[CustomPosition]
    __buttons: deque[InlineKeyboardButton]
    __custom_group: deque[InlineKeyboardButton] = deque()
    position: Position = Position

    def __init__(self, builder, buttons: Collection[InlineKeyboardButton], rows: int = 2):
        """Инициализирует основные копки, которые будут отсортированы по количеству строк."""
        length_buttons = len(buttons)

        if not rows or not isinstance(rows, int): raise ValueError(
            "Число должно быть целочисленным и не быть равным нулю")

        if length_buttons == 0: rows = 1
        elif rows > length_buttons: rows = length_buttons

        self.builder = builder
        self.__buttons = deque(buttons)
        self.__custom_buttons_positions = deque()
        self.rows = rows

    def sort(self):
        count_main_rows = len(self.__buttons)
        result = math.floor(count_main_rows / self.rows)
        result = deque([self.rows]) * result
        remainder_of_division = count_main_rows % self.rows
        if remainder_of_division: result.append(remainder_of_division)

        if self.__custom_buttons_positions:
            for list_buttons in self.__custom_buttons_positions:
                self.__check_positions(list_buttons, result, self.__buttons)

        for button in self.__buttons:
            self.builder.add(button)

        self.builder.adjust(*result)
        return None

    @staticmethod
    def __check_positions(custom: CustomPosition, main_rows: deque, main_buttons: deque) -> None:
        match custom.position:
            case Position.before_main_buttons:
                main_buttons.extendleft(custom.buttons)
                main_rows.appendleft(custom.rows if custom.rows else len(custom.buttons))
            case Position.after_main_buttons:
                main_buttons.extend(custom.buttons)
                main_rows.append(custom.rows if custom.rows else len(custom.buttons))

    def insert_many_custom_buttons(self, *custom_buttons_positions) -> "ButtonSorter":
        self.__custom_buttons_positions.extend(custom_buttons_positions)# = deque(custom_buttons_positions)
        return self

    def insert_one_position_custom_buttons(
            self, buttons: Collection[InlineKeyboardButton], position: Position, rows: int | None = None) -> "ButtonSorter":
        length_buttons = len(buttons)
        if not rows or rows > length_buttons:
            rows = length_buttons
            UserWarning("Количество указанных строк больше чем количество кнопок")

        self.__custom_buttons_positions.append(
            CustomPosition(
                buttons=buttons,
                position=position,
                rows=rows
            )
        )
        return self

    def grouping_buttons_by_position(self, button: InlineKeyboardButton) -> "ButtonSorter":
        self.__custom_group.append(button)
        return self

    def grouping(self, group_position: Position, rows: int | None = None) -> "ButtonSorter":
        length_buttons = len(self.__custom_group)

        if not rows or rows > length_buttons:
            rows = length_buttons
            UserWarning("Количество указанных строк больше чем количество кнопок")

        self.__custom_buttons_positions.append(
            CustomPosition(
                buttons=deque(self.__custom_group),
                position=group_position,
                rows=rows
            )
        )
        self.__custom_group.clear()
        return self
