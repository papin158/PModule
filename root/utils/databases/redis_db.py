import typing
from abc import ABC
from typing import Optional
from .dbcommands import RedisDatabase
import json, aiogram
from prompt import system_prompt
from ...config import JsonUser, UserWait
from redis import Redis


class GettingUsers(RedisDatabase, ABC):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def _user_list(
            self, redis_hash_name: str,
            a_user: aiogram.types.User = None, raw: bool = False, to_json: bool = False) -> \
            Optional[typing.Union[aiogram.types.User, list[aiogram.types.User], list[JsonUser]]]:
        one_or_many = True if a_user else False
        users = await self.connector.hgetall(redis_hash_name)
        if one_or_many:
            return self.__get_user__(one_or_many, a_user=a_user, users=users, raw=raw, to_json=to_json)
        return self.__get_user__(one_or_many, a_user=a_user, raw=raw, users=users, to_json=to_json)

    def __get_user__(self, one: bool, users, raw: bool, a_user, to_json) -> \
            Optional[list[aiogram.types.User]]:
        """
        :param one: Поиск конкретного пользователя.
        :param a_user: Искомый.
        :param users: Место, где ищут.
        :param raw: Получаем ли мы сырые данные.
        :return: Пользователь.
        """
        all_users: list[aiogram.types.User] = []
        for user in users:
            user = self.__get_user_raw(users[user], raw, to_json)
            if one:
                if user.id == a_user.id:
                    return all_users.append(user)
                else:
                    return None
            all_users.append(user)
        return all_users

    @staticmethod
    def __get_user_raw(user, raw, to_json):
        if raw:
            raw = user
        elif to_json:
            raw = json.loads(user)
        else:
            raw = aiogram.types.User.model_validate_json(user)
        return raw


class Context(RedisDatabase):
    __slots__ = ('user',)
    system_prompt = json.loads(system_prompt)

    def __init__(self, user: aiogram.types.User):
        super().__init__()
        self.user = user  # type("Mem", (), {})
        # self.user.id = user_id

    async def add(self, context: dict):
        keys = await self.connector.llen(f"context_user:{self.user.id}")

        if keys > 1000:
            await self.clear_context()
            keys = 0

        if keys == 0:
            await self.connector.rpush(f"context_user:{self.user.id}", system_prompt)

        await self.connector.rpush(f"context_user:{self.user.id}", json.dumps(context))

    async def get(self):
        tmp = []
        context_user = await self.connector.lrange(f"context_user:{self.user.id}", 0, -1)

        for context in context_user:
            tmp.append(json.loads(context))
        return tmp

    async def clear_context(self):
        await self.connector.ltrim(f"context_user:{self.user.id}", -1, 1)


class Users(GettingUsers):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def add(self, user: aiogram.types.User):
        await self.connector.hset(
            "users",
            f"{user.id}",
            f"""{user.model_dump_json()}"""
        )

    async def get(self, user: aiogram.types.User, one: bool = False) -> \
            typing.Union[aiogram.types.User, list[aiogram.types.User]]:
        raw_users = await self.connector.hgetall('users')

        if one:
            find_user = None
            for ruser in raw_users:
                user_args = ruser.split('|')
                if user_args[0] == user.id:
                    find_user = aiogram.types.User.model_validate_json(raw_users[ruser]).as_(user.bot)
            return find_user

        users: list[aiogram.types.User] = []
        for u in raw_users:
            users.append(aiogram.types.User.model_validate_json(u).as_(user.bot))
        return users

    async def get_user_for_id(self, user_id) -> aiogram.types.User:
        return aiogram.types.User.model_validate_json(await self.connector.hget('users', user_id))

    async def get_user_list(
            self,
            a_user: aiogram.types.User = None, raw: bool = False, to_json: bool = False) -> \
            Optional[typing.Union[aiogram.types.User, list[aiogram.types.User], list[JsonUser], list[int]]]:
        return await self._user_list(redis_hash_name='users', a_user=a_user, raw=raw, to_json=to_json)


class BannedUsers(GettingUsers):
    __slots__ = ()

    def __init__(self):
        super().__init__()

    async def add(self, user: aiogram.types.User | dict):
        if isinstance(user, aiogram.types.User):
            user_id = user.id
            user = user.model_dump_json()
        else:
            user_id = user['id']
            user = json.dumps(user)

        await self.connector.hset(
            'banned_users',
            f"{user_id}",
            f"{user}"
        )
        # await self.connector.hdel('users', user_id)

    async def get(
            self,
            a_user: aiogram.types.User = None, raw: bool = False, to_json: bool = False) -> \
            Optional[typing.Union[aiogram.types.User, list[aiogram.types.User], list[JsonUser]]]:
        return await self._user_list(redis_hash_name='banned_users', a_user=a_user, raw=raw, to_json=to_json)

    async def delete(self, user: aiogram.types.User | dict):
        if isinstance(user, aiogram.types.User):
            user_id = user.id
            user = user.model_dump_json()
        else:
            user_id = user['id']
            user = json.dumps(user)

        await self.connector.hset(
            'users',
            f"{user_id}",
            f"{user}"
        )
        await self.connector.hdel('banned_users', user_id)

