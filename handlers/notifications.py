from aiogram import types
from loader import db
from utils import generate_keyboard


async def subscribe_handler(message: types.Message):
    await db.execute('UPDATE users SET notify = ? WHERE tg_id = ?', (True, message.from_user.id))
    await db.commit()
    await message.reply(text='Вы подписались на уведомления', reply_markup=generate_keyboard([None, None, None, True]))


async def unsubscribe_handler(message: types.Message):
    await db.execute('UPDATE users SET notify = ? WHERE tg_id = ?', (False, message.from_user.id))
    await db.commit()
    await message.reply(text='Вы отписались от уведомлений', reply_markup=generate_keyboard([None, None, None, False]))
