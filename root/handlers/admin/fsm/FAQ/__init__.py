from aiogram import Router
from . import faq_create

router = Router()
router.include_routers(faq_create.router)
