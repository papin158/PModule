from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description='Запускает бота'
        ),
        BotCommand(
            command='account',
            description='Настройка бота под себя. Полная версия меню.'
        ),
        BotCommand(
            command='faq',
            description='Частозадаваемые вопросы.'
        ),
        BotCommand(
            command='settings',
            description='Настройка GPT-модели'
        )
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())
