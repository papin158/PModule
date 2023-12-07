import json
from aiogram import types, filters, Router, F

router = Router()

class Check_Message_Args:
    #Получает сообщение, чтобы отправить в консоль данные, которые можно распарсить с помощью F
    @classmethod
    async def get_message(cls, message: types.Message):
        data_message = message.model_dump_json()
        data_message = json.loads(data_message)
        my_data = await cls.get_data_message(data_message)
        for key, value in my_data.items():
            print(f"{key} - {value}")


    #Генерирует методом рекурсии данные, с помощью которых можно обратиться к F
    @classmethod
    async def get_data_message(cls, data_message: dict, prefix: str = '', sep: str = '.') -> dict:
        my_dict = dict()                                                                                    # Создаётся словарь, который нужно распарсить
        for key, value in data_message.items():                                                             # на значения и ключи, учитывая, что внутри значений могут присутствовать ещё словари
            if isinstance(value, dict):                                                                     # Проверяется, существуют ли в значениях ещё словари
                my_dict.update(await cls.get_data_message(data_message=value, prefix=f"{prefix}{key}{sep}"))    # Рекурсивно повторяем цикл, пока словари не закончатся
            else:                                                                                           # Если словарь закончился
                my_dict[f"{prefix}{key}"] = value                                                           # Присваиваем ему путь до значения (например Message.from_user.id - <номер id пользователя>)
        return my_dict


router.message.register(Check_Message_Args.get_message, (F.from_user.id == 5626832979) & F.text == "/data_command")
