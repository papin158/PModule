from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from root.config import config
from root.config.set_commands import set_commands
from root.utils.databases.dbcommands import FAQ_SQLRequests, Context_SQLRequest, SGroups
from root.filters.admins import add_PUser
import asyncio, root, app, collections


async def startup(bot: Bot):
    await set_commands(bot=bot)


async def shutdown(bot: Bot):
    await config.pool[0].close()


async def main():
    # Подключение корневого роутера
    bot = Bot(token=config.config['TOKEN'], parse_mode=ParseMode.HTML)

    dp = Dispatcher()
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    await config.create_pool()
    faq = FAQ_SQLRequests()
    await faq.create_table()
    config.faq_list[0] = collections.deque(await faq.get())
    del faq
    await config.update_privileged_users()
    dp.include_routers(root.router, app.router)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)     # , allowed_updates=["message", "inline_query", "chat_member"])
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
