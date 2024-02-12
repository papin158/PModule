from aiogram.filters import BaseFilter
from aiogram.types import Message as Mes, CallbackQuery as CbQ

from ..config import privileged_users


class IsAdmin(BaseFilter):
    def __call__(self, com: Mes | CbQ):
        return com.from_user.id in privileged_users
