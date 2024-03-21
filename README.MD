## Как настроить
1. Установить зависимости `pip install -r requirements.txt`
2. Скачать google chrome последней версии и скачать chromedriver тоже последней версии. 
Выбрать свою систему и скачать (скорее всего win64) 
https://googlechromelabs.github.io/chrome-for-testing/#stable 
3. Внести путь до скачанного .exe файла в файл `./configs/default.json`
4. Зарегистрироваться на сайте **2captcha.com**, пополнить баланс и получить ключ для работы с API
5. Внести этот ключ в файл `./configs/default.json`
6. Получить токен у бота **@BotFather** в телеграме и внести его в файл `./configs/default.json`
7. В файле `./configs/default.json` поменять **num_workers** на количество потоков, которые вы хотите использовать
8. В файле `./configs/proxies.txt` внести http-прокси в формате **login:pass@ip:port**
9. В файле `./configs/categories.txt` внести категории, которые надо парсить. Категории можно найти тут https://megamarket.ru/catalog/

