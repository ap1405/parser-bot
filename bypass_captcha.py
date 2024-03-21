import logging
from loader import cfg
import os
import random
import requests
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha, TimeoutException


solver = TwoCaptcha(**cfg['anticaptcha'])


def download_image(src, path, proxy=None, cookies=None):
    if proxy:
        proxy['https'] = proxy['http']
    real_cookies = None
    if cookies:
        real_cookies = {}
        for cookie in cookies:
            real_cookies[cookie['name']] = cookie['value']
    headers = {
        'authority': 'megamarket.ru',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    img = requests.get(src, headers=headers, proxies=proxy, cookies=real_cookies)
    if img.status_code == 200:
        with open(path, 'wb') as f:
            f.write(img.content)
        return True
    return False


def get_captcha_text(driver):
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    img_name = 'tmp/screenshot-' + str(random.randrange(0, 10000)) + '.png'
    img_tag = driver.find_element(By.ID, 'captcha_image')
    download_image(img_tag.get_property('src'), img_name, driver.proxy, driver.get_cookies())
    logging.info('Sent captcha to anticaptcha ' + img_name)
    try:
        code = solver.normal(img_name)
    except TimeoutException:
        logging.info('Captcha timeout, trying again...')
        return 'abc321yg'

    os.remove(img_name)
    return code['code']


def solve_captcha(driver, class_name):
    # catalog-collections-selector__title
    while True:
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
            return True
        except WebDriverException:
            logging.info('Captcha is needed, solving...')
            captcha = get_captcha_text(driver)
            driver.find_element(By.NAME, 'captcha').send_keys(captcha)
            driver.find_element(By.NAME, 'submit').click()
            logging.info('Solved captcha')
