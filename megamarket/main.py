import asyncio
from bs4 import BeautifulSoup
import orjson
from loader import cfg
import logging
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time
from bypass_captcha import solve_captcha
from urllib.parse import urlparse


def parse_html(item):
    name = item.find('div', class_='item-title').text.strip()
    mega_id = item.get('id')

    new_price = item.find('div', class_='item-price')
    if new_price:
        new_price = int(new_price.text.replace('₽', '').replace(' ', '').strip())
    else:
        return False

    old_price = item.find('span', class_='crossed-old-price-discount__price')
    if old_price:
        old_price = int(old_price.text.replace('₽', '').replace(' ', '').strip())
    else:
        old_price = new_price

    sber_bonus_tag = item.find('div', class_='money-bonus sm money-bonus_loyalty')
    if not sber_bonus_tag:
        return False
    sber_spasibo = sber_bonus_tag.find('span', class_='bonus-amount')
    if sber_spasibo:
        sber_spasibo = int(sber_spasibo.text.replace(' ', '').strip())
    else:
        print('no sber_spasibo')
        return False

    sber_spasibo_percent = sber_bonus_tag.find('span', class_='bonus-percent')
    if sber_spasibo_percent:
        sber_spasibo_percent = int(sber_spasibo_percent.text.replace('%', '').strip())
    else:
        print('no sber_spasibo_percent')
        return False

    url = 'https://megamarket.ru/' + item.get('router-link-uri')
    percent = item.find('div', class_='discount-percentage__value')
    if percent:
        percent = int(percent.text.replace('%', '').strip())
    else:
        percent = 0
    return {
        'name': name,
        'mega_id': mega_id,
        'percent': percent,
        'old_price': old_price,
        'new_price': new_price,
        'sber_spasibo': sber_spasibo,
        'sber_spasibo_percent': sber_spasibo_percent,
        'url': url,
    }


def parse_page(source, category_url):
    items_parsed = []
    soup = BeautifulSoup(source, 'html.parser')
    items_html = soup.find_all('div', class_='catalog-item')
    for item in items_html:
        item_parsed = parse_html(item)
        if not item_parsed:
            continue
        item_parsed['category'] = category_url
        items_parsed.append(item_parsed)
    return items_parsed


def get_goods(category_url, driver):
    # driver = driver_setup()
    logging.info('getting goods from ' + category_url.split('#')[0])
    try:
        driver.get(category_url)
        solve_captcha(driver, 'catalog-department-header__title')  # solves captcha if present
    except WebDriverException:
        logging.warning('failed to get goods' + category_url.split('#')[0])
        return []

    more_button_class = 'catalog-listing__show-more'
    next_xpath = '//a[@rel="next"]'
    try:
        WebDriverWait(driver, 15).until_not(EC.presence_of_element_located((By.CLASS_NAME, 'r loading')))
    except WebDriverException as e:
        pass
    items_parsed = []
    for i in range(cfg['max_pages_count']):
        logging.debug(f'pressing more button {i} time {category_url.split("#")[0]}')
        try:
            WebDriverWait(driver, 20).until_not(EC.presence_of_element_located((By.CLASS_NAME, 'catalog-skeleton__content_products-item')))
        except WebDriverException as e:
            # print(0, e, category_url.split('#')[0])
            pass
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, next_xpath)))
        except WebDriverException as e:
            # print(1, e, category_url.split('#')[0])
            break
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
        except WebDriverException as e:
            # print(2, e, category_url.split('#')[0])
            continue
        logging.debug(f'parsing goods from page {i} ' + category_url.split('#')[0])
        items_parsed += parse_page(driver.page_source, category_url)
        try:
            element = driver.find_element(By.XPATH, next_xpath)
            driver.execute_script("arguments[0].click();", element)
            logging.debug(f'pressed next button {i} time {category_url.split("#")[0]}')
        except WebDriverException as e:
            # print(3, e, category_url.split('#')[0])
            continue
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'catalog-skeleton__content_products-item')))
        except WebDriverException as e:
            # print(4, e, category_url.split('#')[0])
            continue

    logging.info('done ' + category_url.split('#')[0] + ' parsed ' + str(len(items_parsed)) + ' items')
    return items_parsed


def get_goods_wrapper(category_url, driver):
    try:
        return get_goods(category_url, driver)
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        return []


async def get_categories(driver):
    # without getting categories from site it gets stuck on loading
    # if os.path.exists('categories.json'):
    #     with open('categories.json', 'r', encoding='utf-8') as f:
    #         return orjson.loads(f.read())
    #         ['hydratorState']['PrefetchStore']['componentsInitialState']['catalog']['currentDepartmentCategories']
    driver.get('https://megamarket.ru/catalog/')

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pattern = re.compile(r'"currentDepartmentCategories":\[\{')

    app_cfg = soup.find("script", string=pattern)
    if not app_cfg:
        return []
    app_cfg = app_cfg.text
    app_cfg = app_cfg.replace('window.__APP__=', '').replace('undefined', 'null')
    categories = orjson.loads(app_cfg)['hydratorState']['PrefetchStore']['componentsInitialState']['catalog']['currentDepartmentCategories']
    cats = list(filter(lambda x: not x['collection']['isDepartment'], categories))
    # with open('categories.json', 'w', encoding='utf-8') as f:
    #     f.write(orjson.dumps(categories).decode('utf-8'))
    return cats


async def insert_good(db, good, timing):
    # if good wasn't in db previously then insert it and return True
    cursor = await db.execute('SELECT * FROM goods WHERE mega_id = ?', (good['mega_id'],))
    if await cursor.fetchone():
        await db.execute('''
            UPDATE goods SET
            last_update = ?,
            percent = ?,
            old_price = ?,
            new_price = ?,
            sber_spasibo = ?,
            sber_spasibo_percent = ?
            WHERE mega_id = ?
        ''', (timing, good['percent'], good['old_price'], good['new_price'], good['sber_spasibo'], good['sber_spasibo_percent'], good['mega_id']))
        await cursor.close()
        return False
    await cursor.close()
    await db.execute('''
        INSERT INTO goods (mega_id, name, percent, old_price, new_price, url, category, last_update, sber_spasibo, sber_spasibo_percent) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        good['mega_id'],
        good['name'],
        good['percent'],
        good['old_price'],
        good['new_price'],
        good['url'],
        good['category'],
        timing,
        good['sber_spasibo'],
        good['sber_spasibo_percent']
    ))
    await db.commit()
    return True


async def remove_old_goods(db, url, timing):
    await db.execute('DELETE FROM goods WHERE last_update < ? AND url = ?', (timing, url))
    await db.commit()


def get_final_urls(categories, current_category):
    found_cat = next(item for item in categories if item['collection']['url'] == current_category)
    if not found_cat['collection']['isDepartment']:
        return [current_category]
    return_categories = []
    for cc in [c for c in categories if c['parentId'] == found_cat['id']]:
        if cc['collection']['isDepartment']:
            print('dep', cc['collection']['url'])
            return_categories.extend(get_final_urls(categories, cc['collection']['url']))
        else:
            print('not dep', cc['collection']['url'])
            return_categories.append(cc['collection']['url'])
    return return_categories


def load_categories_from_file():
    with open('./configs/categories.txt', 'r', encoding='utf-8') as f:
        cats = f.read().split('\n')
    needed_categories = [urlparse(c).path for c in cats]
    with open('./configs/categories.json', 'r', encoding='utf-8') as f:
        categories = orjson.loads(f.read())
    return_categories = []
    for nc in needed_categories:
        return_categories.extend(get_final_urls(categories, nc))

    return return_categories


async def worker(db, urls, driver):
    new_goods = []
    for url in urls:
        goods = await asyncio.to_thread(get_goods_wrapper, url, driver)
        timing = int(time.time())
        for good in goods:
            if await insert_good(db, good, timing):
                new_goods.append(good)
        await remove_old_goods(db, url, timing - 10)
    return new_goods


async def main_logic(db, drivers):
    loaded_categories = load_categories_from_file()
    new_goods = []
    # in stock, can use sber spasibo, sort by price
    goods_filter = '#?filters={"1B3347144BD148AF9B0CE4AFF47710F7"%3A["1"]%2C"4CB2C27EAAFC4EB39378C4B7487E6C9E"%3A["1"]}&sort=2'
    urls = [f'https://megamarket.ru{categ}{goods_filter}' for categ in loaded_categories]
    threads = []
    for i, urls_chunk in enumerate([urls[k::len(drivers)] for k in range(len(drivers))]):
        threads.append(asyncio.create_task(worker(db, urls_chunk, drivers[i])))
    for thread in threads:
        new_goods += await thread

    return new_goods


if __name__ == '__main__':
    print(load_categories_from_file())
