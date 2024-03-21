from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiosqlite
import asyncio
import logging
import orjson
from seleniumwire.handler import log as handler_logger
from seleniumwire.server import logger as server_logger
from seleniumwire.storage import log as storage_logger
from seleniumwire.backend import log as backend_logger
from seleniumwire.undetected_chromedriver.webdriver import log as uc_logger

seleniumwire_loggers = [handler_logger, server_logger, storage_logger, backend_logger, uc_logger]

for lgr in seleniumwire_loggers:
    lgr.setLevel(logging.ERROR)


logging.basicConfig(level=logging.INFO)

db: aiosqlite.core.Connection = asyncio.get_event_loop().run_until_complete(aiosqlite.connect('megamarket.sqlite'))

with open('./configs/default.json', 'r') as f:
    cfg = orjson.loads(f.read())

API_TOKEN = cfg['bot_token']

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
