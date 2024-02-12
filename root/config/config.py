import itertools
import os, sys, re, asyncpg, json

from typing import (
    TypedDict, NamedTuple, Optional,
    Any, Iterable, Deque, OrderedDict,
    TypeVar, Union, Final, Mapping)

from redis.asyncio import Redis
from redis import Redis as SyncRedis, DataError
from collections import namedtuple, deque
from dotenv import load_dotenv
from dataclasses import dataclass
from pydantic import BaseModel

load_dotenv()


class Config(NamedTuple):
    TOKEN = os.getenv("TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS = os.getenv("REDIS")
    SyncRedis = os.getenv("REDIS")


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
    'perem_iteration',
    'tech_supports',
    'UserWait',
    'TechSupports',
    'faq_group_list',
    'admin_callbacks',
    'R_SQL'
]


class JsonUser(TypedDict):
    """Те же поля, что и в aiogram.types.User только без функций, не переопределяю класс, потому что будет ошибка при
    загрузке из dump-метода.
    """
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    language_code: Optional[str]
    is_premium: Optional[bool]
    added_to_attachment_menu: Optional[bool]
    can_join_groups: Optional[bool]
    can_read_all_group_messages: Optional[bool]
    supports_inline_queries: Optional[bool]


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
    """
    Пул всех баз данных. Мог бы использовать RabbitMQ или Kafka, но я ленивая жопа.
    """
    PostgreSQL: asyncpg.Pool
    Redis: Redis
    SyncRedis: SyncRedis


class FAQList(TypedDict):
    question: str
    answer: str


@dataclass
class Perem:
    """Перемычка, что по другому я не смог, нужно будет пересмотреть код."""
    i: int = 0
    page: int | None = None
    faq: bool = False


class UserWorkWithSupports(NamedTuple):
    """Костыль, проверяются администраторы, которым была отправлена рассылка с требованием выйти на связь с
    пользователем.
    """
    wait_supports_id: int
    wait_supports_message_id: int


class UserWait(BaseModel):
    """Модель pydantic, которая будет выдавать id-пользователя, ждущего агента тех-поддержки, так же список самих
    агентов тех-поддержки с данными об id как самого агента тех-поддержки, так и отправленного ему сообщения."""
    user_id: "user_id"
    supports_args: Deque[UserWorkWithSupports]
    user_message_id: "support_message_id"


_KT = TypeVar("_KT")  # Спёрто с typing, является шаблоном типа данных для ключа.
_VT = TypeVar("_VT")  # А это для значения словаря.
_T = TypeVar("_T")    # Самый типичный шаблон типа данных, используется, для того, чтобы данные были однотипными.


class RedisDict(OrderedDict[_KT, _VT]):
    """
    Аналог :class:`OrderedDict` в библиотеке typing, только записывает данные напрямую в Redis.
    """
    def __init__(self, hash_name: str, connector: SyncRedis | None = None):
        if not connector:
            self.__connector: SyncRedis = SyncRedis.from_url(url=config.SyncRedis, decode_responses=True)
        else: self.__connector = connector
        self.__hash_name: Final[str] = hash_name
        super().__init__(self.__get_true_type_key_and_value())
        # del locals()['__class__'].__get_true_type_key_and_value

    def __get_true_type_key_and_value(self):
        """
        Формирует правильные данные словаря, без приписки типа данных.
        Потому что Redis возвращает все данные в виде сырой строки.
        :return: Объект класса: :class:`RedisDict`
        """
        for key, value in self.__connector.hgetall(self.__hash_name).items():
            key_var_type, key = key.split('//')
            is_pydantic, value_var_type, value = value.split('//')
            self[eval(f"{key_var_type}(key)")] = eval(f"{value_var_type if is_pydantic == '1' else ''}{'.model_validate_json' if is_pydantic == '1' else 'json.loads'}(value)")
        return self

    def clear(self) -> None:
        """Очищает словарь"""
        self.__connector.delete(self.__hash_name)
        super(RedisDict, self).clear()

    def pop(self, __key: _KT) -> _VT:
        """Удаляет элемент по ключу"""
        self.__delitem_from_redis(__key)
        return super(RedisDict, self).pop(__key)

    def popitem(self, last: bool = ...) -> tuple[_KT, _VT]:
        """Удаляет первый или последний элемент словаря.
        :param last: Уточняющий параметр, нужно удалить первый или последний ключ, поумолчанию - да.
        :return: Ключ, значение в виде кортежа: :class:`tuple[_KT, _VT]`
        """
        tmp = super(RedisDict, self).popitem(last)
        self.__delitem_from_redis(tmp[0])
        return tmp

    def __delitem_from_redis(self, item):
        """
        Удаляет параметр напрямую из базы данных.
        Нужен для того, чтобы не прописывать каждый раз обращение к базе.
        Используется только эта фунция внутри класса.
        :param item: Удаляемый параметр, который будет приведён в соответствующий вид, как он хранится в базе.
        """
        self.__connector.hdel(self.__hash_name, f"{type(item).__name__}//{item}")

    def __delitem__(self, item):
        """Удаляет элемент в словаре по ключу."""
        self.__delitem_from_redis(item)
        super(RedisDict, self).__delitem__(item)

    # def __getitem__(self, item):
    #     return super(RedisDict, self).__getitem__(item)

    def __setitem__(self, key, value):
        """
        Записывает значение по ключу.
        Записываются только стандартные элементы, с записью типа данных, которые могут быть приведены к строке,
        а также данные классы от pydantic приведённые к типу json.
        :param key: Ключ, по которому идёт запись.
        :param value: Значение, которое должно быть записано.
        """
        search = re.search("class", str(value))
        is_pydantic = 0
        value_type = type(value).__name__
        value_dict = value
        if BaseModel.__mro__[0] in value.__class__.__bases__:
            is_pydantic = 1
            value = value.model_dump_json()
        elif value.__class__.__name__ not in {**sys.modules['builtins'].__dict__, **sys.modules['collections'].__dict__}\
        or search:
            raise DataError("Такой тип данных недопустим")
        self.__connector.hset(
            self.__hash_name, f"{type(key).__name__}//{key}",
            f"{is_pydantic}//{value_type}//{value if is_pydantic else json.dumps(value)}")
        return super(RedisDict, self).__setitem__(key, value_dict)

    # def update(self, __m: Mapping[_KT, _VT], **kwargs: _VT) -> None:
    #     for key, value in itertools.chain(__m.items(), kwargs):
    #         self.__setitem__(key, value)


class RedisSet(set[_T]):
    __connector: SyncRedis

    def __init__(self, set_name: str, connector: object | None = None):
        self._set_name = set_name
        self.__connector = connector if connector else SyncRedis.from_url(url=config.SyncRedis, decode_responses=True)
        super().__init__(map(int, self.__connector.smembers(self._set_name)))

    def __delitem__(self, key):
        self.discard(key)

    def __delattr__(self, item):
        self.discard(item)

    def discard(self, element: _T) -> None:
        self.__connector.srem(self._set_name, element)
        return super(RedisSet, self).discard(element)

    def pop(self) -> _T:
        temp = super(RedisSet, self).pop()
        self.__connector.srem(self._set_name, temp)
        return temp

    def remove(self, element: _T) -> None:
        result = super(RedisSet, self).remove(element)
        self.__connector.srem(self._set_name, element)
        return result

    def clear(self) -> None:
        self.__connector.delete(self._set_name)
        return super(RedisSet, self).clear()

    def add(self, element: _T) -> None:
        self.__connector.sadd(self._set_name, element)
        return super(RedisSet, self).add(element)

    def update(self, *s: Iterable[_T]) -> None:
        temp = set(*[a for a in s])
        self.__connector.sadd(self._set_name, *temp)
        return super(RedisSet, self).update(*s)


class TechSupports:
    tech_supports_in_work: RedisSet["support_id"]
    tech_supports: set["support_id"]
    _new_dict: RedisDict[int, UserWait]
    __connector: SyncRedis

    def __init__(self, hash_name: str, set_name: str, **kwargs):
        self.__hash_name = hash_name
        self.__connector = SyncRedis.from_url(url=config.SyncRedis, decode_responses=True)
        self._new_dict = RedisDict(hash_name, self.__connector)
        self.tech_supports = set()
        self.tech_supports_in_work = RedisSet(set_name, self.__connector)

    @property
    def user_wait(self) -> RedisDict[int, UserWait]:
        return self._new_dict

    @user_wait.setter
    def user_wait(self, user_wait: Union[dict[int, UserWait], UserWait]):
        if isinstance(user_wait, dict):
            self.__add_more(user_wait)
        else:
            self.__add_one(user_wait)

    def __add_one(self, user: UserWait):
        self._new_dict[user.user_id] = user

    def __add_more(self, users: dict[int, UserWait]):
        for key, value in users.items():
            self._new_dict[key] = value

    @user_wait.deleter
    def user_wait(self):
        self.__connector.hdel(self.__hash_name)


faq_group_list = RedisDict[str, FAQList]('faq_group_lists')
support_id, user_id, support_message_id = int, int, int
tech_supports = TechSupports(hash_name='users_wait', set_name='tech_supports_in_work')
pool = Pool
faq_list: list[FAQList] = []
group_subordinate = {}
privileged_users: dict[..., PrivilegedUser] = {}
admin_callbacks: set[str] = set()
groups: dict[..., Group] = {}
perem_iteration = Perem()

R_SQL = namedtuple("R_SQL", "question answer")


async def create_pool():
    """
    Создаются объекты классов баз данных, которые можно использовать в любом месте программы,
    заранее не проинициализированному.
    """
    pool.PostgreSQL = await asyncpg.create_pool(dsn=config.DATABASE_URL)
    pool.Redis = await Redis.from_url(config.REDIS, decode_responses=True)
    pool.SyncRedis = SyncRedis.from_url(config.SyncRedis, decode_responses=True)


async def update_privileged_users(
        new_group: Optional[str] = None,
        new_user: Optional[NewUser] = None,
        higher_user_groups: Optional[Iterable] = None
):
    """
    Пользователи, группы и привилегии извлекаются из базы-данных PostgreSQL, потому что данные, сохранённые в
    реляционной базе данных являются важными и потеря данных из Redis не опасна.
    """
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

    privileged_users.clear()
    tech_supports.tech_supports.clear()

    for items in users_groups:
        privileged_users[items['puser']] = {'user_groups': items['user_groups'],
                                            'user_subordinate_groups': items['user_subordinate_groups'],
                                            'super_user': items['super_user'],
                                            'add_or_delete_group': items['add_or_delete_group'],
                                            'update_user_group': items['update_user_group'],
                                            'update_permissions_subgroup': items['update_permissions_subgroup'],
                                            'update_faq': items['update_faq']
                                            }
        if privileged_users[items['puser']]['update_faq']:
            tech_supports.tech_supports.add(int(items['puser']))

    del users_privileged
    del users_groups
    del pusers
