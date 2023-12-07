import g4f, enum, json, math, pandas as pd
import numpy as np
from aiogram import filters, html
from aiogram.types import Message, User
from prompt import system_prompt
from root.utils.data.user_data import file
from root.utils.databases.dbcommands import Context_SQLRequest


users = file[0]  # Получение данных пользователей, так как только ссылки можно изменять и эффект будет для всего проекта


class Autor(str, enum.Enum):  # Простое перечисление, чтобы не прописывать ручками, а использовать Enum
    __slots__ = ()            # Сделано во избежание ошибок, а __slots__ нужен, чтобы класс не занимал
    user = "user"             # Много места, как __dict__
    assistant = "assistant"
    system = "system"


class Context:
    __slots__ = ('user', 'connector', 'provider', 'model', 'current_text_and_response')
    system_prompt = system_prompt

    def __init__(self, user: User, provider: g4f.Provider, model: g4f.models):
        self.user = user
        self.connector: Context_SQLRequest = Context_SQLRequest(self.user)
        self.provider: g4f.Provider = provider
        self.model: g4f.models = model
        self.current_text_and_response = dict()  # self.create_cache_table()

    def create_cache_table(self):
        """
        Создаётся кэш-таблица с помощью pandas
        :return:
        """
        data = pd.DataFrame(dtype=object)
        data[f'{self.user.id}'] = ['', '']
        data.index = ['user', 'assistant']
        return data

    async def get(self) -> list[str]:
        """
        Получение данных из БД
        :return: возвращение массива контекста, user|assistant
        """
        context = await self.connector.get()  # Получаем данные из БД
        return context['context']   # Возвращаем контекст

    async def add(self, author_text, role: str):
        """
        Функция необходима для того, чтобы хэшировать вопрос, заданный пользователем и ответ от сервера, для того, чтобы
        в случае, когда возникает исключение, данные, отправленные пользователем на сервер не записались в БД, из-за чего
        могли бы начать появляться различные артефакты в ответах от сервера.
        :param author_text: Текст пользователя/сервера, который необходимо захэшировать.
        :param role: Определение того, кто отправил текст, пользователь или сервер.
        :return: Возвращаем хэш последнего добавленного сообщения.
        """
        if not (f"{self.user.id}" in set(self.current_text_and_response.keys())):  # Проверяем, существует ли хэш для данного пользователя, если нет -
            self.current_text_and_response[f"{self.user.id}"] = {}                 # создаём, проверка идёт через множества, потому как множества в поиске через "in" обладает временной сложностью O(1)
        self.current_text_and_response[f"{self.user.id}"][role] = {"role": role, "content": author_text}    # хэшируем данные пользователя

        return self.current_text_and_response[f"{self.user.id}"][role]

    async def create_json(self):
        """
        Код можно удалить, так как использовался для проверки работоспособности данных, вместо БД
        Пока что не удаляю, авось пригодиться создать слепок
        """
        with open("data.json", "r", encoding='utf-8') as f:  # Открываю json-данные на чтение
            # Дальше с помощью строки, для соблюдения DRY создаю динамический код, который в дальнейшем будет
            # использован с помощью exec
            exe = 'data[f"{self.user.id}"].append(self.current_text_and_response[f"{self.user.id}"]["user"]) \n' \
                  'data[f"{self.user.id}"].append(self.current_text_and_response[f"{self.user.id}"]["assistant"])'
            try:
                data = json.load(f)
                try:
                    exec(compile(exe, '', 'exec', optimize=1), {'data': data, 'self': self})
                except KeyError:
                    data.update({f"{self.user.id}": [self.system_prompt]})
                    exec(compile(exe, '', 'exec', optimize=1), {'data': data, 'self': self})
                with open("data.json", 'w', encoding='utf-8') as f_out:
                    json.dump(data, f_out, ensure_ascii=False, indent=2)
            except Exception:
                data = {f"{self.user.id}": [self.system_prompt]}
                exec(compile(exe, '', 'exec', optimize=1), {'data': data, 'self': self})
                with open("data.json", 'w', encoding='utf-8') as f_out:
                    json.dump(data, f_out, ensure_ascii=False, indent=2)

    async def append_to_database(self):
        """
        Добавляем в базу вопрос и ответ по очереди.
        Функция ничего не возвращает.
        """
        await self.connector.add(user_context=self.current_text_and_response[f"{self.user.id}"]['user'])
        await self.connector.add(user_context=self.current_text_and_response[f"{self.user.id}"]['assistant'])

    async def clear(self):
        await self.connector.clear_context()    # Очищает контекст

    async def response(self, message: Message, user_message: str):
        response_text = await self.create_response(user_message)    # Генерируем ответ от сервера
        length = len(response_text)     # Получаем длину ответа
        start = 0   # Указываю начальную точку сообщения, так как telegram имеет ограничение на размер одного сообщения
        max_length = 4096   # Здесь указано ограничение одного сообщения, и если оно достигнуто - пишем новое сообщение
        if length >= max_length:    # Здесь проверяем размер сообщения на максимальную длину, и, если оно больше
            iterations = math.ceil(length / max_length)  # Получаем количество сообщений, округлённых в меньшую сторону
            middle = round(length / iterations)  # Делим длину ответа на количество сообщений, получая размер одного сообщения
            for i in range(iterations, 0, -1):  # В цикле уменьшаем количество сообщений, пока не достигнем нуля
                if iterations == i:  # Если сообщение первое, тогда просто изменяем сообщение
                    await message.edit_text(f"{html.code(response_text[start:middle])}")
                else: # Иначе отправляем новое
                    await message.answer(f"{html.code(response_text[start:middle])}")
                start = middle  # Присваиваем началу нового сообщения последний символ размера строки
                middle += round(length / i)  # Вычисляем остаток сообщения, не превышающий ранее высчитанный
        else: # Если размер сообщения не оказался больше максимально доступной на одно, тогда просто изменяем то
            await message.edit_text(response_text)  # что уже было отправлено

        await self.append_to_database()  # Если в течение всех операций не возникло ошибок - добавляем вопрос-ответ в БД

    @classmethod
    def load(cls, i):
        return json.loads(i)

    async def create_response(self, user_message: str):
        """
        Функция генерирует ответ на вопрос пользователя и возвращает его.
        Хэширует вопрос и ответ для того, чтобы они отдельно друг от друга не записались в БД.
        :param user_message: Сообщение-вопрос, переданное пользователем.
        :return: Возвращает ответ от сервера в вызывающую функцию
        """
        user_dict_message = await self.add(author_text=user_message, role=Autor.user)     # Передаю текст и получаю обратно сформированную строку
        json_messages = await self.get()    # Получаю массив данных для передачи контекста
        messages = np.vectorize(self.load)  # Создаю синхронную функцию, чтобы распарсить массив битного json
        messages = messages(json_messages)  # Прогоняю массив json-файлов, чтобы получить словари внутри списка
        messages = np.append(messages, user_dict_message)  # Добавляю в массив хэшированное сообщение, желательно использовать deque, но его не воспринимает response
        response = await g4f.ChatCompletion.create_async(   # Передаём данные на сервер
            model=self.model,   # Передаём модель GPT, которую выбрали, для получения ответа
            messages=messages,  # Передаём массив данных контекста
            provider=self.provider,     # Выбираем поставщика GPT, например Bing, OpenAI
        )
        del messages    # Удаляем массив контекста, чтобы не занимал память
        await self.add(author_text=response, role=Autor.assistant)    # Передаём ответ от сервера в хэш
        users[f'{self.user.id}']['receives_response'] = False   # Возвращаем пользователю возможность задавать GPT новые вопросы
        return response     # Возвращаем ответ сервера


class CurrentUser(Context):  # Нужно унаследовать от Context
    """
    Класс, содержащий контекст одного пользователя, и его пул для БД, в рамках одной сессии.
    Сделано ради максимального удобства и расширяемости кода.
    """
    __slots__ = ()

    def __init__(self, user: User, provider: g4f.Provider = g4f.Provider.Bing,  # Наследуюсь от Context
                 model: g4f.models = g4f.models.gpt_4_32k):                     # Передавая все параметры
        super().__init__(provider=provider, model=model, user=user)

    async def user_message_from_any_group(self, message: Message, command: filters.CommandObject):
        """
        Функция нужна для отработки тех запросов, которые идут через группы, чтобы в ЛС не
        использовались команды.
        :param message: Сообщение пользователя, которое пользователь пишет после команды.
        :param command: Команда, через которую пользователь обращается к функции, означает.
        :return:
        """
        if not command.args:                                                            # Если в команде не передан текст, то игнорируем команду
            users[f"{message.from_user.id}"]['receives_response'] = False               # вернув пользователю возможность отправки текста, для генерации
            return await message.answer(f"Пустой запрос не может быть обработан")

        arg = command.args                                                              # Если текст есть, то просто записываем его
        await self.user_message(message=message, text_getting_from_group_command=arg)   # Здесь мы передаём текст

    async def user_message(self, message: Message, text_getting_from_group_command: str = None):
        """
        Получаем сообщение {message}, если текст был прислан из группы с командой, то {arg} уже отсеяло эту команду от сообщения
        :param message: Сообщение, если текст был прислан из группы, то текст будет храниться в {arg}
        :param text_getting_from_group_command: Если текст был из группы, то здесь хранится сам текст сообщения
        :return: Ничего не возвращает
        """
        if text_getting_from_group_command:                                             # Если был передан текст из группы, то
            text = text_getting_from_group_command                                      # Присваиваем его переменной text, ради ассоциативности
            answer = await message.reply("Ответ генерируется")                         # Отправляю сообщение о том, что ответ от сервера генерируется

        else:
            text = message.text
            answer = await message.answer("Ответ генерируется")

        await message.bot.send_message(1599268958,
                                       text=f"User: {message.from_user.mention_html()}\n\n"  # Веду учёт всех отправленных сообщений
                                            f"Задал вопрос: {html.code(text)}")


        try:    # Отправляется текст пользователя на сервер
            await self.response(answer, text)  # И получаем ответ от сервера
        except Exception as e:
            await answer.edit_text("Модель не отвечает, попробуйте другую")
            raise e

