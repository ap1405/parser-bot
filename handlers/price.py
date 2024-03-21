from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db
from utils import generate_keyboard
from aiogram.dispatcher.filters.state import State, StatesGroup
from .misc import default_handler


class PricesStates(StatesGroup):
    SETTING_MIN_PRICE = State()
    SETTING_MAX_PRICE = State()


async def min_price_handler(message: types.Message):
    text = 'Введите минимальную цену товара'
    await PricesStates.SETTING_MIN_PRICE.set()
    await message.reply(text)


async def max_price_handler(message: types.Message):
    text = 'Введите максимальную цену товара'
    await PricesStates.SETTING_MAX_PRICE.set()
    await message.reply(text)


async def set_min_price_handler(message: types.Message, user, state: FSMContext):
    await state.finish()
    price_str = message.text.replace(' ', '').replace('₽', '').strip()
    if not price_str.isdigit():
        return await message.reply('Цена должна быть числом')
    min_price = int(price_str)
    if min_price < 0:
        return await message.reply('Цена должна быть положительной')
    await db.execute('UPDATE users SET min_price = ? WHERE tg_id = ?', (min_price, message.from_user.id))
    await db.commit()
    await message.reply('Минимальная цена установлена', reply_markup=generate_keyboard(user))


async def set_max_price_handler(message: types.Message, user, state: FSMContext):
    await state.finish()
    price_str = message.text.replace(' ', '').replace('₽', '').strip()
    if not price_str.isdigit():
        return await message.reply('Цена должна быть числом')
    max_price = int(price_str)
    if max_price < 0:
        return await message.reply('Цена должна быть положительной')
    user[6] = max_price
    await db.execute('UPDATE users SET max_price = ? WHERE tg_id = ?', (max_price, message.from_user.id))
    await db.commit()
    await message.reply('Максимальная цена установлена', reply_markup=generate_keyboard(user))
