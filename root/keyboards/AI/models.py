import numpy as np, enum, math
from typing import Optional
from aiogram import types
from aiogram.utils import keyboard
from aiogram.filters.callback_data import CallbackData
from root.keyboards import exe, all_keyboards_for_main_manu, Iteration_CallbackData, MainMenu
from g4f.Provider import *

all_gpt_providers = np.array([
    BaseProvider,  AsyncProvider,  AsyncGeneratorProvider,
    RetryProvider, Acytoo,  AiAsk, Aibn,  Aichat,
    Ails, Aivvm,  AiService, AItianhu, AItianhuSpace,
    Aivvm, Bard, Berlin,  Bing, Bestim, ChatBase, ChatForAi, Chatgpt4Online,
    ChatgptAi, ChatgptDemo, ChatgptDuo, ChatgptFree,
    ChatgptLogin, ChatgptX, Cromicle, DeepInfra,
    CodeLinkAva, DfeHub, EasyChat, Forefront,
    FakeGpt, FreeGpt, GPTalk, GptChatly, GptForLove,
    GetGpt, GptGo,  GptGod, Hashnode,
    H2o, HuggingChat, Liaobots, Llama2, Lockchat,
    Myshell, MyShell, Opchatgpts,
    Raycast, OpenaiChat, OpenAssistant,
    PerplexityAi, Phind, Theb, Vercel, Vitalentum,
    Wewordle, Ylokh, You, Yqcloud, Equing, FastGpt,
    Wuguokai, V50, GeekGpt], dtype=object)

# config.admin_callbacks.add("gpt")


class GPTVersion(enum.Enum):
    __slots__ = ()
    gpt_3 = 3
    gpt_4 = 4


class Defaults:
    __slots__ = ()
    @classmethod
    def kb_started(cls):
        return np.array([
            types.KeyboardButton(text='')
        ])


class Inline:
    __slots__ = ()
    @classmethod
    def kb_gpt(cls):
        markup = keyboard.InlineKeyboardBuilder()

        markup.row(
            keyboard.InlineKeyboardButton(text=f"Если хотите использовать GPT нажмите сюда", callback_data="gpt")
        )
        return markup

    @classmethod
    def kb_gpt4(cls):
        markup = keyboard.InlineKeyboardBuilder()

        markup.row(
            keyboard.InlineKeyboardButton(text=f"Если хотите использовать GPT4 нажмите сюда", callback_data="gpt4")
        )
        markup.row(
            keyboard.InlineKeyboardButton(text=f"GPT41 ", callback_data="gpt41")
        )
        return markup

    @classmethod
    async def kb_gpt_provider(cls, version, *, depth):
        CURRENT_DEPTH = depth
        markup = keyboard.InlineKeyboardBuilder()
        len_rows = 3
        custom_b = 1    #Потому что у меня есть только кнопка back
        i = 0

        def add_but(m):
            nonlocal i
            if i != 0:
                markup.button(text=f"{m}", callback_data=GPTCallback(version=version, provider=m, id=i, current_depth=CURRENT_DEPTH+1))
            i += 1

        gpt_names = np.vectorize(lambda m: m.__name__)
        gpt_names = gpt_names(await cls.choice_gpt(version))

        gpt_buttons = np.vectorize(add_but)
        gpt_buttons = gpt_buttons(gpt_names)

        markup.button(text="Назад", callback_data=GPTCallback(version=version, provider="", id=i + 1,
                                                              current_depth=CURRENT_DEPTH - 1))

        if gpt_buttons.size < len_rows*2:
            len_rows -= 1

        exec(exe, {'builder': markup, 'buttons': gpt_buttons, 'len_rows': len_rows,
                   'math': math, 'np': np, 'custom_b': custom_b})

        return markup.as_markup()

    @classmethod
    async def kb_choice_gpt(cls, *, depth):
        CURRENT_DEPTH = depth
        markup = keyboard.InlineKeyboardBuilder()
        markup.button(text=f"GPT_3", callback_data=GPTCallback(version=GPTVersion.gpt_3.value, provider='-1', id=0,
                                                               current_depth=CURRENT_DEPTH+1))
        markup.button(text=f"GPT_4", callback_data=GPTCallback(version=GPTVersion.gpt_4.value, provider='-1', id=0,
                                                               current_depth=CURRENT_DEPTH+1))

        markup.button(text=f"Назад", callback_data=GPTCallback(version=-1, provider='-1', id=-1,
                                                               current_depth=CURRENT_DEPTH - 1))

        markup.adjust(2, 1)

        return markup.as_markup()

    @classmethod
    async def choice_gpt(cls, version):
        var = eval("all_gpt_{version}".format(version=version))
        return var

    @classmethod
    async def kb_settings(cls, *, depth):
        CURRENT_DEPTH = depth
        builder = keyboard.InlineKeyboardBuilder()
        builder.button(text=f"Изменение версии/модели", callback_data=GPTCallback(version=-1,
                                                                                  provider='-1', id=0,
                                                                                  current_depth=CURRENT_DEPTH + 1))
        builder.button(text='Очистить контекст', callback_data=GPTCallback(clear_context=True))
        builder.button(text=f"Назад", callback_data=MainMenu(main=True))
        builder.adjust(2, 1)

        return builder.as_markup()


class GPTCallback(CallbackData, prefix="gpt"):
    version: Optional[int] = None
    provider: Optional[str] = ''
    id: Optional[int] = None
    current_depth: int = 0
    clear_context: bool = False


def define_np(dynamic, variable, condition=''):
    var = eval("np.vectorize(lambda m: {condition} m.{dynamic})".format(dynamic=dynamic, condition=condition), {"np": np})
    var = var(variable)
    var = variable[var]
    return var


all_gpt_working = np.vectorize(lambda m: m.working)
all_gpt_working = all_gpt_working(all_gpt_providers)
all_gpt_working = all_gpt_providers[all_gpt_working]

all_gpt_not_need_auth = define_np("needs_auth", all_gpt_working, 'not')
all_gpt_3 = define_np("supports_gpt_35_turbo", all_gpt_not_need_auth)
all_gpt_4 = define_np("supports_gpt_4", all_gpt_not_need_auth)

all_keyboards_for_main_manu.append(
    Iteration_CallbackData(description="Настройка GPT",
                           callback=GPTCallback(version=-1, provider='-1', id=-1, current_depth=0))
)
