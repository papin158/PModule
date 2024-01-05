from aiogram import Router
from . import __init_file__, __init_dirs__

router = Router()
router.include_routers(__init_file__.router, __init_dirs__.router)
