import enum
from pprint import pprint

from aiogram import BaseMiddleware, types
from typing import Awaitable, Callable, Any
from ...config import privileged_users, admin_callbacks


class AllCallbacks(enum.Enum):
    admin_menu = 'add_or_delete_group'
    group_edit = 'update_permissions_subgroup'
    user_editable = 'update_user_group'
    adm_faq = 'update_faq'


class CheckAdminFuncs(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.CallbackQuery, dict[Any, Any]], Awaitable[Any]],
            event: types.CallbackQuery,
            data: dict[str, Any]
    ) -> Any:
        callback = event.data.split(":")[0]
        in_state = callback in admin_callbacks
        admin_callbacks.discard('admin_menu')
        admin = event.from_user.id in privileged_users
        user_id = event.from_user.id

        if not in_state or (admin and privileged_users[user_id][eval(f'AllCallbacks.{callback}.value')]):
            return await handler(event, data)

        return await event.message.edit_text("Вы не администратор, вам нельзя пользоваться этим.")
