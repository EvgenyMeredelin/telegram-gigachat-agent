import black
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, Message, Update
from aiohttp import web
from decouple import config

from agents import *


BOT_TOKEN = config("BOT_TOKEN")
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = Dispatcher()


def format_black(response: requests.Response) -> str:
    """
    Наглядное структурированное представление ответа с содержимым типа
    application/json.
    """
    return black.format_str(repr(response.json()), mode=black.Mode())


@dispatcher.message(F.text)
async def handle_text_message(message: Message):
    """Обработка текстового сообщения пользователя. """

    # агент-диспетчер определяет имя целевого агента
    agent_name = supervisor.handle_message(message)
    agent = menu.get(agent_name, OFFTOP_SENTINEL)

    # оффтоп: сообщение пользователя не вызывает ни один доступный агент
    if agent == OFFTOP_SENTINEL:
        await message.answer(fallback_answer)

    # целевой агент извлекает из сообщения данные и отправляет их в API
    else:
        response = agent.handle_message(message)
        content_type = response.headers["content-type"]

        if content_type == "application/json":
            await message.answer(format_black(response))
        elif content_type == "image/png":
            image = BufferedInputFile(response.content, "image.png")
            await message.answer_photo(image)


routes = web.RouteTableDef()


@routes.post(f"/{BOT_TOKEN}")
async def handle_webhook(request: web.Request):
    """Обработка webhook из Telegram. """
    if str(request.url).split("/")[-1] == BOT_TOKEN:
        request_content = await request.json()
        update = Update(**request_content)
        await dispatcher.feed_update(bot, update)
        return web.Response(text="OK")
    return web.Response(status=403)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host="0.0.0.0", port=int(config("PORT")))
