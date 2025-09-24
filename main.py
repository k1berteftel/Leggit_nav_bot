import asyncio
from typing import Any, Awaitable, Callable, Dict
from cachetools import TTLCache
import logging

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update,
                           User, FSInputFile, TelegramObject, InputMediaPhoto)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_data.config import load_config, Config


config: Config = load_config()


format = '[{asctime}] #{levelname:8} {filename}:' \
         '{lineno} - {name} - {message}'

logging.basicConfig(
    level=logging.DEBUG,
    format=format,
    style='{'
)


logger = logging.getLogger(__name__)


bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def back_main(clb):
    await asyncio.sleep(20)
    photo = InputMediaPhoto(media=FSInputFile('media/Menu.png'), caption='Выберите интересующий вас пункт')
    await clb.message.edit_media(media=photo, reply_markup=main_keyboard)


class ReturnMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        clb = event
        result = await handler(event, data)

        task_name = 'return_menu'
        for task in asyncio.all_tasks():
            if task.get_name() == task_name:
                task.cancel()
        task = asyncio.create_task(back_main(clb))
        task.set_name(task_name)

        return result


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.storage = TTLCache(
            maxsize=1000,
            ttl=2.5
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        clb = event
        event_from_user: User = data.get('event_from_user')
        if self.storage.get(event_from_user.id):
            await clb.answer('❗️Пожалуйста подождите несколько секунд и попробуйте снова')
            return
        self.storage[event_from_user.id] = True
        return await handler(event, data)


main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='❓Кто я', callback_data='about'),
            InlineKeyboardButton(text='👨‍💻Услуги', callback_data='services')
        ],
        [InlineKeyboardButton(text='🔗Блог (live)', url='https://t.me/Leggit_live')],
        [InlineKeyboardButton(text='🗂Мои отзывы', url='https://t.me/Leggit_revs')],
        [InlineKeyboardButton(text='💼Студия', url='https://t.me/Leggit_Studio')],
        [InlineKeyboardButton(text='💬Написать мне', url='https://t.me/Leggit_dev')]
    ]
)


@dp.callback_query(F.data == 'about')
async def show_about(clb: CallbackQuery):
    text = ('👋Привет, меня зовут <b>Кирилл</b>, мне 18 лет, и я — Python-developer '
            '(Технический специалист) под брендом <b>Leggit</b>.\n\n<em>Я помогаю предпринимателям и '
            'бизнесменам создавать эффективные решения для автоматизации процессов, увеличения продаж и '
            'улучшения взаимодействия с аудиторией через Telegram-боты и веб-приложения .</em>\n\n'
            '<b>❓Почему выбирают меня?</b>\n\n<b>• Глубокая экспертиза в Telegram-технологиях :</b>\n'
            'Я специализируюсь на разработке ботов и веб-приложений, которые работают на результат. '
            'Будь то воронка продаж, CRM-система или полноценный магазин в Telegram — я создаю продукты, '
            'которые приносят реальную прибыль.\n<b>• Молодой, но опытный: </b>\nНесмотря на возраст, '
            'я уже реализовал десятки успешных проектов для бизнеса. Мой подход сочетает современные '
            'технологии и креативное мышление.\n<b>• Индивидуальный подход:</b>\n Я не просто пишу код — '
            'я изучаю ваш бизнес, чтобы предложить решение, которое решает именно ваши задачи.')
    photo = InputMediaPhoto(media=FSInputFile('media/Me.png'), caption=text)
    await clb.message.edit_media(media=photo, reply_markup=main_keyboard)


@dp.callback_query(F.data == 'services')
async def show_services(clb: CallbackQuery):
    text = ('<b><u>Что я предлагаю?</u></b>\n\n<b>• 📊Боты для инфобизнеса</b>: создание воронок продаж, '
            'CRM-систем и автоматизированных решений для прогрева аудитории, увеличения конверсий и '
            'управления клиентами.\n• <b>⚙️Автоматизация бизнес-процессов</b>: оптимизация рутинных задач, управление '
            'базами данных и построение систем, которые работают за вас 24/7.\n<b>• 🤖Интеграция ИИ</b>: '
            'внедрение умных алгоритмов для анализа данных, прогнозирования поведения клиентов и '
            'персонализации взаимодействия.\n<b>• 💸Монетизация продуктов</b>: '
            'разработка решений для продажи товаров, услуг или контента через Telegram, включая '
            'полноценные магазины и системы подписок.')
    photo = InputMediaPhoto(media=FSInputFile('media/Service.png'), caption=text)
    await clb.message.edit_media(media=photo, reply_markup=main_keyboard)


async def _on_startup():
    await bot.send_photo(
        chat_id=config.bot.channel_id,
        photo=FSInputFile('media/Menu.png'),
        caption='Выберите интересующий вас пункт',
        reply_markup=main_keyboard
    )


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.callback_query.outer_middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ReturnMiddleware())

    #dp.startup.register(_on_startup)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


