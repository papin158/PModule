from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from root import config
from root.utils.databases.dbcommands import FAQ_SQLRequests, Context_SQLRequest, SGroups
from root.middlewares.check_user import CheckUser
from root.filters.admins import add_PUser
import asyncio, root, app, collections


async def startup(bot: Bot):
    await config.set_commands(bot=bot)


async def shutdown(bot: Bot):
    await config.pool.PostgreSQL.close()


async def main():
    # Подключение корневого роутера
    storage = RedisStorage.from_url(config.config.REDIS)
    bot = Bot(token=config.config.TOKEN, parse_mode=ParseMode.HTML)

    dp = Dispatcher(storage=storage)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    await config.create_pool()
    faq = FAQ_SQLRequests()
    await faq.create_table()
    config.faq_list.extend(await faq.get())
    del faq
    await config.update_privileged_users()

    dp.update.middleware.register(CheckUser())
    dp.include_routers(root.router, app.router)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)     # , allowed_updates=["message", "inline_query", "chat_member"])
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
