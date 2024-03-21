from aiogram import Dispatcher
from .notifications import *
from .misc import *
from .price import *
from .percentage import *


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(subscribe_handler, text='Подписаться на уведомления')
    dp.register_message_handler(unsubscribe_handler, text='Отписаться от уведомлений')

    dp.register_message_handler(min_price_handler, text='Изменить минимальную цену')
    dp.register_message_handler(max_price_handler, text='Изменить максимальную цену')

    dp.register_message_handler(set_min_price_handler, state=PricesStates.SETTING_MIN_PRICE)
    dp.register_message_handler(set_max_price_handler, state=PricesStates.SETTING_MAX_PRICE)

    dp.register_message_handler(min_percentage_handler, text='Изменить минимальный процент скидки')
    dp.register_message_handler(set_min_percentage_handler, state=PercentageStates.SETTING_MIN_PERCENT)

    dp.register_message_handler(default_handler)
