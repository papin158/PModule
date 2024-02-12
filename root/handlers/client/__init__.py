from aiogram import Router
from . import faq
from . import contact

router = Router()
router.include_routers(faq.router, contact.router)
__all__ = ['router']
