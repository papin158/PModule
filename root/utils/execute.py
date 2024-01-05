import aiogram, aiogram.filters.callback_data, typing, inspect, asyncio, concurrent.futures


async def always_answer(
        message: typing.Union[aiogram.types.Message, aiogram.types.CallbackQuery],
        text: str,
        reply_markup: typing.Optional[
                typing.Union[aiogram.types.InlineKeyboardMarkup, aiogram.types.ReplyKeyboardMarkup,
                aiogram.types.ReplyKeyboardRemove, aiogram.types.ForceReply]
            ] = None,
) -> aiogram.types.Message:
    if isinstance(message, aiogram.types.CallbackQuery):
        message = message.message

    return await message.answer(text, reply_markup=reply_markup)


def execute(message: typing.Union[aiogram.types.Message, aiogram.types.CallbackQuery],
            text: str,
            inline_message_id: typing.Optional[str] = None,
            parse_mode: typing.Optional[str] = aiogram.types.UNSET_PARSE_MODE,
            entities: typing.Optional[typing.List[aiogram.types.MessageEntity]] = None,
            disable_web_page_preview: typing.Optional[bool] = aiogram.types.base.UNSET_DISABLE_WEB_PAGE_PREVIEW,
            disable_notification: typing.Optional[bool] = None,
            protect_content: typing.Optional[bool] = aiogram.types.base.UNSET_PROTECT_CONTENT,
            reply_to_message_id: typing.Optional[int] = None,
            allow_sending_without_reply: typing.Optional[bool] = None,
            reply_markup: typing.Optional[
                typing.Union[aiogram.types.InlineKeyboardMarkup, aiogram.types.ReplyKeyboardMarkup,
                aiogram.types.ReplyKeyboardRemove, aiogram.types.ForceReply, typing.Callable]
            ] = None,
            callback_data: typing.Optional[typing.Union[aiogram.filters.callback_data.CallbackData,
                                           typing.List, typing.Tuple, typing.Set]] = None,
            advanced_args: typing.Optional[dict] = None,
            schrodinger_message:
            typing.Optional[typing.Union[aiogram.types.Message, aiogram.types.CallbackQuery]] = None,
            **kwargs: typing.Any
            ) -> typing.Awaitable[typing.Union[aiogram.types.Message, aiogram.types.CallbackQuery]]:
    """
    Нужен для проверки на изменение сообщения, если было по кнопки - значит будет сообщение изменяться,
    если нет, значит будет отправляться ответ на сообщение.
    :param schrodinger_message: Сообщение Шрёдингера, либо оно есть, либо нет. 
    Перекрывает собой message, если существует.
    :param advanced_args: Дополнительные аргументы
    :param callback_data:
    :param text: Сам текст, который нужно отправить.
    :param inline_message_id:
    :param parse_mode: Какой режим форматирования будет использоваться HTML, Markdown или MarkdownV2
    :param entities:
    :param disable_web_page_preview:
    :param disable_notification:
    :param protect_content: Защищённый контент.
    :param reply_to_message_id: Отвечать на конкретный id-сообщения.
    :param allow_sending_without_reply: Можно ли отвечать на это сообщение.
    :param reply_markup: Кнопки.
    :param message: Само сообщение или коллбэк.
    :return: Возвращается сообщение.
    """
    # reply_markup должен быть <Callable>, т.е. не вызываясь через await <Awaitable> и без вызова функции ()
    #  <Coroutine>
    callback_data = update_callback(callback_data)

    if isinstance(message, aiogram.types.Message):
        # Если schrodinger_message существует, то перекрывает собой message.
        if schrodinger_message: message = schrodinger_message
        reply_markup = create_from_callable_to_sync_markup(reply_markup=reply_markup, callback_data=callback_data,
                                                           advanced_args=advanced_args, message=message)
        return message.answer(
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            **kwargs
        )
    elif isinstance(message, aiogram.types.CallbackQuery):
        # Если schrodinger_message существует, то перекрывает собой call.message.
        if schrodinger_message:
            message = type("message", (), {})
            message.message = schrodinger_message
        reply_markup = create_from_callable_to_sync_markup(reply_markup=reply_markup, callback_data=callback_data,
                                                           advanced_args=advanced_args, message=message.message)

        return message.message.edit_text(
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
            inline_message_id=inline_message_id,
            **kwargs
        )
    else:
        raise TypeError("Это не сообщение")


def you_dont_have_permission(message: aiogram.types.Message):
    bot = message.bot
    chat_id = message.chat.id
    return bot.edit_message_text(chat_id=chat_id, text="У Вас нет доступа к этой команде", reply_markup=None)


def is_privileged(
        user_id: int,
        users_groups: typing.Any,
        admin_command: bool = False,
        support_command: bool = False,
        privileged_group: typing.Optional[
            typing.Union[typing.List[str], typing.Tuple[str], typing.Set[str], str]] = None,
        including_or: typing.Optional[bool] = None,
        exclusive_or: typing.Optional[bool] = None,
        including_and: typing.Optional[bool] = None,
) -> bool:
    if not (privileged_group or admin_command or support_command): return False

    len_groups = len(privileged_group) - 1

    if admin_command or support_command:
        if admin_command and support_command: privileged_group = {'admins', 'supports'}
        elif admin_command: privileged_group = 'admins'
        else: privileged_group = 'supports'

    if isinstance(privileged_group, typing.List | typing.Set | typing.Tuple) and len(privileged_group) == 1: privileged_group = privileged_group[0]

    if isinstance(privileged_group, typing.List | typing.Set | typing.Tuple) and len(privileged_group) > 1 and (including_or or exclusive_or or including_and):
        iteration = iter(privileged_group)
        next(iteration)
        temp = None
        try:
            if exclusive_or and not (including_and or including_or):

                for n, group in enumerate(privileged_group):
                    if n == len_groups: break
                    temp = users_groups[group].symmetric_difference(users_groups[next(iteration)])
            elif including_or and not (including_and or exclusive_or):
                for n, group in enumerate(privileged_group):
                    if n == len_groups: break
                    temp = users_groups[group].union(users_groups[next(iteration)])
            elif including_and and not (including_or or exclusive_or):
                for n, group in enumerate(privileged_group):
                    if n == len_groups: break
                    temp = users_groups[group].intersection(users_groups[next(iteration)])
            else: return False
            return user_id in temp
        except KeyError: return False
    elif isinstance(privileged_group, str):
        try:
            return user_id in users_groups[privileged_group]
        except KeyError: return False
    else: return False


def awaitable_reply_markup(
    reply_markup: typing.Callable,
    callback_data: typing.Optional[typing.Union[aiogram.filters.callback_data.CallbackData,
                                typing.Set]] = None,
    advanced_args: typing.Optional[dict] = None,
    message: aiogram.types.Message|None = None
) -> typing.Union[aiogram.types.InlineKeyboardMarkup, aiogram.types.ReplyKeyboardMarkup,
                  aiogram.types.ReplyKeyboardRemove, aiogram.types.ForceReply]:
    """

    :param message:
    :param advanced_args:
    :param reply_markup: Вызываемая, асинхронная функция.
    :param callback_data: Коллбэк-дата, по данным которой нужно всё установить в функцию.
    :return: Возвращается корутина с внедрёнными параметрами.
    """
    if not callback_data: return reply_markup(depth=0)

    is_callback = False
    bra = ''
    # Получаю все параметры вызываемой функции, и создаю из него множества из-за выигрыша в скорости
    params = set(inspect.signature(reply_markup).parameters)    #

    if isinstance(callback_data, aiogram.filters.callback_data.CallbackData):
        temp = {*callback_data.model_fields.keys()}
        is_callback = True
    else: temp = callback_data

    if advanced_args:  # сложность операций = O(1) + O(1*n) + O(n) = O(1) + 2 * O(n)
        for callback in advanced_args:  # Просто перебор O(n)
            if (callback not in temp) and callback in params:  # Проверка значения на вхождение, сложность O(1); значения в множествах - хеш
                bra += f'{callback}=advanced_args["{callback}"],'  # Но это находится в цикле поэтому O(n)

    temp = temp & params
    if is_callback:
        for callback in temp:
            bra += f'{callback}=callback_data.{callback},'
    else:
        for callback in temp:
            bra += f'{callback}=True,'

    return eval(f'reply_markup({bra})')


def update_callback(callback_data: typing.Any) -> typing.Set:
    if isinstance(callback_data, aiogram.filters.callback_data.CallbackData):
        callback_data = callback_data
    elif isinstance(callback_data, typing.Set):
        # callback_data.add('the_main')
        callback_data = callback_data
    elif isinstance(callback_data, typing.Tuple) or isinstance(callback_data, typing.List):
        callback_data = {*callback_data}
        # callback_data.add('the_main')
    return callback_data


def create_from_callable_to_sync_markup(
        reply_markup: typing.Union[
                      aiogram.types.InlineKeyboardMarkup, aiogram.types.ReplyKeyboardMarkup,
                      aiogram.types.ReplyKeyboardRemove, aiogram.types.ForceReply, typing.Callable
                      ],
        callback_data: typing.Union[
                       aiogram.filters.callback_data.CallbackData,
                       typing.List, typing.Tuple, typing.Set
                       ],
        advanced_args: typing.Optional[dict] = None,
        message: typing.Optional[aiogram.types.Message] = None
) -> typing.Union[aiogram.types.InlineKeyboardMarkup, aiogram.types.ReplyKeyboardMarkup,
                  aiogram.types.ReplyKeyboardRemove, aiogram.types.ForceReply]:
    if isinstance(reply_markup, typing.Callable):

        async def aa():
            return await awaitable_reply_markup(reply_markup=reply_markup, callback_data=callback_data,
                                                advanced_args=advanced_args, message=message)

        # Функция, которую будем вызывать в отдельном потоке
        def run_async_function():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(aa())
            loop.close()
            return result

        # Запускаем асинхронную функцию в отдельном потоке
        future = concurrent.futures.ThreadPoolExecutor().submit(run_async_function)

        # Блокируем выполнение синхронного кода, ожидая результата
        result = future.result()

        # Передаём в клавиатуру результат
        reply_markup = result
    return reply_markup
