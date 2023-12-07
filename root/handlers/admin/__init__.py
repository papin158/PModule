from aiogram import Router
from . import data_message, supports, fsm, FAQ

router = Router()
router.include_routers(data_message.router, FAQ.router, fsm.router)  # , supports.router)
