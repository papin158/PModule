from aiogram import F, Router, types
from aiogram.filters import ChatMemberUpdatedFilter, MEMBER

router = Router()


async def check_users(message: types.Message):
    print(types.ChatMember)
    await message.answer("Бульк")


router.message.register(check_users)
