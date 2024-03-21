from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from loader import cfg
from selenium.common.exceptions import WebDriverException
import seleniumwire.undetected_chromedriver as uc
from bypass_captcha import solve_captcha


WORKERS_COUNTER = 0


def driver_setup():
    global WORKERS_COUNTER
    while True:
        options = uc.ChromeOptions()
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--incognito')
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option(
            'prefs', {'profile.default_content_setting_values.notifications': 1}
        )
        with open('./configs/proxies.txt', 'r') as f:
            proxies = f.readlines()
        proxy = proxies[WORKERS_COUNTER % len(proxies)].strip()
        WORKERS_COUNTER += 1
        proxy_options = {
            'proxy': {
                'http': f"http://{proxy}",
                'https': f"http://{proxy}"
            }
        }

        driver = uc.Chrome(
            driver_executable_path=cfg['driver_path'],
            options=options,
            version_main=116,
            seleniumwire_options=proxy_options
        )
        driver.maximize_window()
        try:
            # without this line it gets stuck later on loading
            driver.get('https://megamarket.ru/catalog/')
            solve_captcha(driver, 'catalog-department-header__title')  # solves captcha if present
            break
        except WebDriverException:
            logging.warning('Driver error, restarting. Google\'s issue...')
            driver.stop_client()
            driver.quit()

    return driver


def generate_keyboard(user):
    return ReplyKeyboardMarkup([
        [
            KeyboardButton(text='Отписаться от уведомлений' if user[3] else 'Подписаться на уведомления')
        ],
        [
            KeyboardButton(text='Изменить минимальную цену'),
            KeyboardButton(text='Изменить максимальную цену'),
            KeyboardButton(text='Изменить минимальный процент скидки'),
        ],
        [
            KeyboardButton(text='Профиль'),
        ]
    ], resize_keyboard=True, one_time_keyboard=False, is_persistent=True)


async def create_table(db):
    await db.execute('''
        CREATE TABLE IF NOT EXISTS goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mega_id TEXT UNIQUE,
            name TEXT,
            percent INTEGER,
            old_price INTEGER,
            new_price INTEGER,
            url TEXT,
            category TEXT,
            last_update INTEGER,
            sber_spasibo INTEGER,
            sber_spasibo_percent INTEGER
        );
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE
        );
    ''')
    await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id INTEGER UNIQUE,
                    join_date INTEGER,
                    notify BOOLEAN,
                    min_percent INTEGER,
                    min_price INTEGER,
                    max_price INTEGER
                );
            ''')
    await db.commit()
