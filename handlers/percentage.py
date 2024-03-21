from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import db
from utils import generate_keyboard
from aiogram.dispatcher.filters.state import State, StatesGroup
from .misc import default_handler


class PercentageStates(StatesGroup):
    SETTING_MIN_PERCENT = State()


async def min_percentage_handler(message: types.Message):
    text = 'Введите минимальную скидку'
    await PercentageStates.SETTING_MIN_PERCENT.set()
    await message.reply(text)


async def set_min_percentage_handler(message: types.Message, user, state: FSMContext):
    await state.finish()
    percentage_str = message.text.replace(' ', '').replace('%', '').strip()
    if not percentage_str.isdigit():
        return await message.reply('Процент должна быть числом')
    min_percentage = int(percentage_str)
    if min_percentage < 0:
        return await message.reply('Процент должен быть положительным')
    await db.execute('UPDATE users SET min_percent = ? WHERE tg_id = ?', (min_percentage, message.from_user.id))
    await db.commit()
    await message.reply('Минимальный процент установлен', reply_markup=generate_keyboard(user))
