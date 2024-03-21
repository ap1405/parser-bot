from aiogram import types
from utils import generate_keyboard


async def default_handler(message: types.Message, user: tuple):
    text = 'Привет! Твой аккаунт:\n' \
           f'Уведомления: <b>{"Включены" if user[3] else "Отключены"}</b>\n' \
           f'Минимальный процент скидки: <b>{user[4]}%</b>\n' \
           f'Минимальная цена: <b>{user[5]}₽</b>\n' \
           f'Максимальная цена: <b>{user[6]}₽</b>'
    await message.reply(text, reply_markup=generate_keyboard(user), parse_mode='HTML')
