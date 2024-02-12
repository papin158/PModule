__author__ = 'papin158'

import aiogram.types
from aiogram import Dispatcher, Bot, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from root import config
from root.middlewares.contact_support import Contact
from root.middlewares.throttling import Throttling
from root.utils.databases.dbcommands import FAQ_SQLRequests, Context_SQLRequest, SGroups
from root.middlewares.check_user import CheckUserUpdate, close_any_state, is_admin
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

    # dp.message.middleware.register(Throttling(storage))
    dp.update.outer_middleware.register(CheckUserUpdate())
    dp.callback_query.middleware.register(is_admin.CheckAdminFuncs())
    dp.callback_query.register(close_any_state, F.data.in_({'close_state', 'экстренно_закрыть'}))
    dp.include_routers(root.router, app.router)
    dp.update.middleware.register(Contact(bot))

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)     # , allowed_updates=["message", "inline_query", "chat_member"])
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
