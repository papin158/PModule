from aiogram import types, Router, filters, F
import math
from text import text
from . import main_commands
from . import admin
from . import client

__all__ = \
    [
        "router"
    ]


router = Router()


async def lorem(message: types.Message):
    length = len(text)
    start = 0
    max_length = 4096
    iterations = math.ceil(length / max_length)
    middle = round(length / iterations)
    for i in range(iterations, 6, -1):
        tmp = text[start:middle]
        await message.answer(tmp)
        start = middle
        middle += round(length / i)


async def send_photo(message: types.Message):
    await message.answer("Da")


router.message.register(lorem, filters.Command("lorem"))
router.message.register(send_photo, F.photo)
router.include_routers(main_commands.router, admin.router, client.router)
