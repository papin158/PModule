from aiogram import Router
from . import data_message,  add_user_privilege

router = Router()
router.include_routers(
    add_user_privilege.router,
    data_message.router
)
