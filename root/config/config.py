import numpy as np, asyncpg
from collections import namedtuple
from dotenv import load_dotenv
import os

config = {

}

load_dotenv()
config["TOKEN"] = os.getenv("TOKEN")
config["DATABASE_URL"] = os.getenv("DATABASE_URL")


__all__ = [
    'pool',
    'faq_list',
    'privileged_users',
    'super_admins',
    'R_SQL'
]

pool = np.array([None], dtype=object)
faq_list = np.array([None], dtype=object)
privileged_users = {
    "admins": set(),
    "supports": set()
                    }

super_admins = set()

R_SQL = namedtuple("R_SQL", "question answer")


async def create_pool():
    pool[0]: asyncpg.Pool = await asyncpg.create_pool(dsn=config['DATABASE_URL'])
                                                      #user='physics', password='MaRkiz851', database='test_db',
                                                      #host='localhost', port=5432)


async def update_privileged_users():
    from root.utils.databases.dbcommands import PUsers
    pusers = PUsers()
    await pusers.create_table()
    privileged_users['admins'].update(*(await pusers.get('admins', "user_id")))
    privileged_users['supports'].update(*(await pusers.get('supports', "user_id")))