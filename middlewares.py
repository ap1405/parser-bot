from loader import db, cfg
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
import time


async def save_user(user_id):
    cursor = await db.execute('SELECT * FROM users WHERE tg_id = ?', (user_id,))
    user = await cursor.fetchone()
    if user:
        await cursor.close()
        return user
    await db.execute('''
        INSERT INTO users (tg_id, join_date, notify, min_percent, min_price, max_price) 
        VALUES (?, ?, ?, ?, ?, ?)''', (
        user_id,
        int(time.time()),
        True,
        cfg['default_user_config']['min_percent'],
        cfg['default_user_config']['min_price'],
        cfg['default_user_config']['max_price']
    ))
    await db.commit()
    await cursor.close()
    user = await db.execute('SELECT * FROM users WHERE tg_id = ?', (user_id, ))
    return await user.fetchone()


class SavingMiddleware(BaseMiddleware):
    @staticmethod
    async def on_pre_process_message(message: types.Message, data: dict):
        data['user'] = await save_user(message.from_user.id)

    @staticmethod
    async def on_pre_process_callback_query(query: types.CallbackQuery, data: dict):
        data['user'] = await save_user(query.from_user.id)
