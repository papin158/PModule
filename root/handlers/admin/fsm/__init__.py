from aiogram import Router
from . import FAQ

router = Router()
router.include_routers(FAQ.router)
