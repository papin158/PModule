from aiogram import Router
from . import supports, fsm, FAQ

router = Router()
router.include_routers(
    FAQ.router,
    fsm.router
)
