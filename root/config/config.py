import asyncpg
from redis.asyncio import Redis
from collections import namedtuple
from typing import TypedDict, NamedTuple, Literal, Optional, Sequence, Any, TYPE_CHECKING, Iterable
from dotenv import load_dotenv
from dataclasses import dataclass
import os

if TYPE_CHECKING:
    from aiogram.types import User as AGUser

load_dotenv()


class Config(NamedTuple):
    TOKEN = os.getenv("TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS = os.getenv("REDIS")


config = Config


__all__ = [
    'pool',
    'faq_list',
    'privileged_users',
    'group_subordinate',
    'groups',
    'PrivilegedUser',
    'Group',
    'create_pool',
    'config',
    'update_privileged_users',
    'JsonUser',
    'R_SQL'
]


class JsonUser(TypedDict):
    id: int
    """Unique identifier for this user or bot. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier."""
    is_bot: bool
    """:code:`True`, if this user is a bot"""
    first_name: str
    """User's or bot's first name"""
    last_name: Optional[str]
    """*Optional*. User's or bot's last name"""
    username: Optional[str]
    """*Optional*. User's or bot's username"""
    language_code: Optional[str]
    """*Optional*. `IETF language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_ of the user's language"""
    is_premium: Optional[bool]
    """*Optional*. :code:`True`, if this user is a Telegram Premium user"""
    added_to_attachment_menu: Optional[bool]
    """*Optional*. :code:`True`, if this user added the bot to the attachment menu"""
    can_join_groups: Optional[bool]
    """*Optional*. :code:`True`, if the bot can be invited to groups. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    can_read_all_group_messages: Optional[bool]
    """*Optional*. :code:`True`, if `privacy mode <https://core.telegram.org/bots/features#privacy-mode>`_ is disabled for the bot. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    supports_inline_queries: Optional[bool]
    """*Optional*. :code:`True`, if the bot supports inline queries. Returned only in :class:`aiogram.methods.get_me.GetMe`."""


class Group(TypedDict):
    add_or_delete_group: bool
    update_user_group: bool
    update_permissions_subgroup: bool
    update_faq: bool
    subordinate_groups: list


class PrivilegedUser(TypedDict):
    user_groups: list
    user_subordinate_groups: list
    super_user: bool
    add_or_delete_group: bool
    update_user_group: bool
    update_permissions_subgroup: bool
    update_faq: bool


class NewUser(NamedTuple):
    user: Any
    group: str
    super_user: bool


@dataclass
class Pool:
    PostgreSQL: asyncpg.Pool
    Redis: Redis


pool = Pool
faq_list: list[dict[Literal['question', 'answer']]] = []
# faq_list = dict[typing.Literal['faq_list'], ...]
group_subordinate = {}
privileged_users: dict[..., PrivilegedUser] = {}
groups: dict[..., Group] = {}

R_SQL = namedtuple("R_SQL", "question answer")


async def create_pool():
    pool.PostgreSQL = await asyncpg.create_pool(dsn=config.DATABASE_URL)
    pool.Redis = await Redis.from_url(config.REDIS, decode_responses=True)


async def update_privileged_users(
        new_group: Optional[str] = None,
        new_user: Optional[NewUser] = None,
        higher_user_groups: Optional[Iterable] = None
):
    from root.utils.databases.postgresql import SGroups  # , Groups
    sgroups = SGroups()
    await sgroups.create_table()
    user_groups = await sgroups.get_all()

    if not user_groups:
        del user_groups
        return

    await update_groups(new_group)
    if higher_user_groups:
        for group in higher_user_groups:
            await sgroups.add(group, new_group)
    await update_user_list(new_user)

    del sgroups


async def update_groups(new_group: Optional[str] = None):
    from root.utils.databases.postgresql import Groups
    all_groups = Groups()
    await all_groups.create_table()

    if new_group:
        await all_groups.add(new_group)

    groups_list = await all_groups.get()

    for items in groups_list:
        groups[items['user_group']] = {'add_or_delete_group': items['add_or_delete_group'],
                                       'update_user_group': items['update_user_group'],
                                       'update_permissions_subgroup': items['update_permissions_subgroup'],
                                       'update_faq': items['update_faq'],
                                       'subordinate_groups': items['subordinate_groups'] if items['subordinate_groups'][0] else []}

    del groups_list
    del all_groups

async def update_user_list(new_user: Optional[NewUser] = None):
    from root.utils.databases.dbcommands import Privileged
    from root.utils.databases.dbcommands import PUsers
    users_privileged = Privileged()
    pusers = PUsers()
    await pusers.create_table()
    await users_privileged.create_table()

    if new_user:
        await pusers.add(new_user.user.id, super_user=new_user.super_user)
        await users_privileged.add(user_id=new_user.user.id, user_group=new_user.group)

    users_groups = await users_privileged.get_users_privileges()

    for items in users_groups:
        privileged_users[items['puser']] = {'user_groups': items['user_groups'],
                                            'user_subordinate_groups': items['user_subordinate_groups'],
                                            'super_user': items['super_user'],
                                            'add_or_delete_group': items['add_or_delete_group'],
                                            'update_user_group': items['update_user_group'],
                                            'update_permissions_subgroup': items['update_permissions_subgroup'],
                                            'update_faq': items['update_faq']
                                            }
    del users_privileged
    del users_groups
    del pusers
