from aiogram import Router
from . import handlers, keyboards, utils

router = Router()
router.include_routers(handlers.router)
__all__ = ['router']


