import json
import typing
import aiogram
from pydantic import BaseModel
from prompt import system_prompt
from asyncpg import Connection, Pool
from redis.asyncio import Redis as RConnection
from root.config.config import pool
from abc import ABCMeta, abstractmethod


class DataBase(metaclass=ABCMeta):
    __slots__ = ('connector',)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataBase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.connector: Pool = pool.PostgreSQL

    @abstractmethod
    async def create_table(self): ...

    @abstractmethod
    async def add(self, *args, **kwargs): ...

    @abstractmethod
    async def get(self, *args, **kwargs): ...


class RedisDatabase(metaclass=ABCMeta):
    __slots__ = ('connector', )
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisDatabase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.connector: RConnection = pool.Redis

    @abstractmethod
    async def add(self, *args, **kwargs): ...

    @abstractmethod
    async def get(self, *args, **kwargs): ...


class Context_SQLRequest(DataBase):
    __slots__ = ('user',)

    def __init__(self, user: aiogram.types.User):
        super().__init__()
        self.user: aiogram.types.User = user

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."Context"
                   (user_id bigint PRIMARY KEY,
                   user_fullname varchar(255),
                   context JSONB[]);
                '''

        await self.connector.execute(query)

    async def add(self, user_context):
        query = '''
        INSERT INTO public."Context" (user_id, user_fullname, context)
        VALUES($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET user_fullname=$2, context=public."Context".context || excluded.context;
        '''

        await self.connector.execute(query, self.user.id, self.user.full_name, [json.dumps(user_context)])

    async def get(self):
        query = '''SELECT * FROM public."Context" WHERE user_id=$1'''
        user = await self.connector.fetchrow(query, self.user.id)
        if not user and not user['context']:
            await self.clear_context()
            user = await self.get()
        return user

    async def clear_context(self):
        query = '''INSERT INTO public."Context" (user_id, user_fullname, context)
                   VALUES ($2, null, $1) 
                   ON CONFLICT (user_id) DO UPDATE SET context=$1'''
        await self.connector.execute(query, [system_prompt], self.user.id)


class FAQ_SQLRequests(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."FAQ"
                           (question varchar(255) PRIMARY KEY,
                            answer TEXT
                           );
                        '''
        await self.connector.execute(query)

    async def add(self, question, answer):
        query = '''INSERT INTO public."FAQ" (question, answer)
                    VALUES ($1, $2)
                    ON CONFLICT (question) DO UPDATE SET answer=excluded.answer
                    RETURNING *;
                '''
        return await self.connector.fetch(query, question, answer)

    async def get(self) -> list[typing.OrderedDict[typing.Literal['question'], typing.Literal['answer']], ...]:
        query = '''SELECT * FROM public."FAQ" ORDER BY question;
                '''
        return await self.connector.fetch(query)

    async def delete(self, question):
        query = '''DELETE FROM public."FAQ" WHERE question=$1;
                '''

        await self.connector.execute(query, question)


class PUsers(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."PUsers"(
                   user_id bigint PRIMARY KEY,
                   super_user bool NOT NULL DEFAULT False
                   );
                '''

        await self.connector.execute(query)

    async def add(self, user_id: int, super_user: bool = False):
        query = '''INSERT INTO public."PUsers" (user_id, super_user)
                   VALUES ($1, $2)
                   ON CONFLICT (user_id) DO UPDATE SET super_user=excluded.super_user
                   RETURNING *;
                '''
        return await self.connector.fetch(query, user_id, super_user)

    async def get(self, user_id, what_select: str = '*'):
        query = f'''SELECT {what_select} FROM public."PUsers" WHERE user_id=$1;
                '''

        return await self.connector.fetch(query, user_id)

    async def delete(self, user_id):
        query = '''DELETE FROM "PUsers" WHERE user_id=$1;
                '''
        return self.connector.execute(query, user_id)


class SGroups(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."SGroups"(
                   user_group varchar(255) PRIMARY KEY,
                   subordinate_groups varchar(255)[]
                   );
                '''
        await self.connector.execute(query)

    async def add(self, group: str, subordinate_groups: typing.Set[str]):
        query = '''INSERT INTO public."SGroups" (user_group, subordinate_groups) VALUES ($1, $2) 
                   ON CONFLICT (user_group) DO UPDATE SET subgroups=excluded.subgroups;
                '''
        return await self.connector.fetch(query, group, subordinate_groups)

    async def get(self, user_group):
        query = '''SELECT * FROM public."SGroups" WHERE user_group=$1;
                '''
        return await self.connector.fetchrow(query, user_group)

    async def get_all(self):
        query = '''SELECT * FROM public."SGroups";
                '''

        return await self.connector.fetch(query)

    async def del_(self, user_group):
        query = '''DELETE FROM public."SGroups" WHERE user_group=$1;
                '''

        await self.connector.execute(query, user_group)


class Privileged(DataBase):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS public."Privileges"(
                   puser bigint REFERENCES public."PUsers" ON DELETE CASCADE,
                   user_group varchar(255) REFERENCES public."Groups" ON DELETE CASCADE,
                   PRIMARY KEY (puser, user_group)
);
                        '''
        await self.connector.execute(query)

    async def add(self, user_id: int, user_group: str):
        query = '''INSERT INTO public."Privileges"(puser, user_group)
                   VALUES($1, $2) ON CONFLICT (puser, user_group) DO NOTHING
                   RETURNING *;
                '''
        return await self.connector.fetchrow(query, user_id, user_group)

    async def get(self, user_group, what_select: str = "*"):
        query = f'''SELECT {what_select} FROM public."Privileges" WHERE user_group=$1;
                '''

        return await self.connector.fetch(query, user_group)

    async def get_user_privileges(self, user_id: int):
        query = '''SELECT array_agg("Privileges".user_group) as user_groups FROM public."Privileges" JOIN public."SGroups" 
                   ON public."SGroups".user_group=public."Privileges".user_group WHERE puser=$1;
                '''

        return await self.connector.fetch(query, user_id)

    async def get_users_privileges(self):
        # query = '''SELECT "Privileges".puser, array_agg("Privileges".user_group) as user_groups FROM public."Privileges" JOIN public."SGroups"
        #            ON public."SGroups".user_group=public."Privileges".user_group GROUP BY "Privileges".puser;
        #         '''

        query = '''SELECT DISTINCT "Privileges".puser, array_agg(DISTINCT "Privileges".user_group) as user_groups,
                   array_agg(DISTINCT "SGroups".subordinate_group) FILTER ( WHERE "SGroups".subordinate_group IS NOT NULL ) as user_subordinate_groups,
                   bool_or(super_user) as super_user,
                   bool_or("Groups".add_or_delete_group) as add_or_delete_group, bool_or(update_user_group) as update_user_group,
                   bool_or("Groups".update_permissions_subgroup) as update_permissions_subgroup, bool_or(update_faq) as update_faq
                       FROM "Privileges"
                       LEFT JOIN "SGroups" ON "SGroups".user_group = "Privileges".user_group
                       JOIN "Groups" ON "Groups".user_group="Privileges".user_group
                       JOIN "PUsers" PU ON "Privileges".puser = PU.user_id GROUP BY "Privileges".puser;
                '''

        return await self.connector.fetch(query)

    async def delete(self, user_id: int, user_group: str = ''):
        query = f'''DELETE FROM "Privileges" WHERE puser=$1 {f"AND user_group='{user_group}'" if user_group else ''}; 
                '''

        return await self.connector.execute(query, user_id)
