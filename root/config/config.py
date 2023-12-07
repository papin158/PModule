import numpy as np, asyncpg
from collections import namedtuple
from dotenv import load_dotenv
import os, typing

config = {

}

load_dotenv()
config["TOKEN"] = os.getenv("TOKEN")
config["DATABASE_URL"] = os.getenv("DATABASE_URL")


__all__ = [
    'pool',
    'faq_list',
    'privileged_users',
    'group_subordinate',
    'R_SQL'
]

pool = np.array([None], dtype=object)
faq_list = np.array([None], dtype=object)
group_subordinate = np.array([None], dtype=object)
privileged_users = {}


R_SQL = namedtuple("R_SQL", "question answer")


async def create_pool():
    pool[0]: asyncpg.Pool = await asyncpg.create_pool(dsn=config['DATABASE_URL'])


async def update_privileged_users():
    from root.utils.databases.dbcommands import PUsers, SGroups, Privileged
    pusers = PUsers()
    sgroups = SGroups()
    privileged = Privileged()
    await pusers.create_table()
    await sgroups.create_table()
    await privileged.create_table()
    user_groups = await sgroups.get_all()
    if not user_groups: return

    for group in user_groups:
        privileged_users[group[0]] = set(*(await privileged.get(group[0], "user_id")))

    del privileged
    del sgroups
    del pusers
