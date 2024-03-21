from aiogram import executor
import asyncio
from handlers import register_handlers
from loader import bot, dp, db, cfg
import logging
from megamarket import main_logic
from middlewares import SavingMiddleware
import signal
from utils import create_table, driver_setup


async def generate_table():
    await create_table(db)


async def checking_loop(drivers):
    goods = await main_logic(db, drivers)
    logging.info(f'Notifying users')
    for good in goods:
        cursor = await db.execute('SELECT * FROM users '
                                  'WHERE '
                                  'notify = TRUE AND min_price <= ? AND ? <= max_price AND min_percent <= ?',
                                  (good['new_price'], good['new_price'], good['sber_spasibo_percent']))
        users = await cursor.fetchall()
        await cursor.close()

        for user in users:
            try:
                await bot.send_message(user[1], f'Новый товар: {good["name"]}\n'
                                                f'Цена: {good["new_price"]}₽\n'
                                                f'Можно списать сберспасибо: {good["sber_spasibo"]}₽\n'
                                                f'Процент который можно списать: {good["sber_spasibo_percent"]}%\n'
                                                f'Ссылка: {good["url"]}', disable_web_page_preview=True)
            except:  # user blocked bot or user blocked
                pass
    logging.info(f'Notified users')


def turn_off_driver(driver):
    driver.stop_client()
    driver.close()
    driver.quit()
    driver.service.process.send_signal(signal.SIGTERM)
    return True


async def check_for_discounts():
    drivers = []
    try:
        logging.info('Starting drivers')
        drivers_coroutines = [asyncio.to_thread(driver_setup) for _ in range(cfg['num_workers'])]
        drivers = await asyncio.gather(*drivers_coroutines)
        # await main_logic(db, drivers)  # loading current state
        while True:
            logging.info('Starting checking for discounts')
            await checking_loop(drivers)
            logging.info(f"Sleeping for {cfg['sleep_time']} seconds")
            await asyncio.sleep(cfg['sleep_time'])
    except KeyboardInterrupt:
        logging.info('Stopping drivers')
        await asyncio.gather(*[asyncio.to_thread(turn_off_driver, driver) for driver in drivers])


async def on_startup(_):
    dp.setup_middleware(SavingMiddleware())
    register_handlers(dp)
    await generate_table()
    asyncio.create_task(check_for_discounts())


async def on_shutdown(_):
    await db.close()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
