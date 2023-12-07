from aiogram import Router
from . import faq

router = Router()
router.include_routers(faq.router)
__all__ = ['router']
