# Подключение к базе данных
import psycopg2

import Links
from DataBase_config import host, user, password, db_name
connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# Подключение библиотек для парсинга
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidSelectorException

# Подключение встроенных библиотек
import time
from datetime import datetime
import functools

# Импорт ссылок новостей
import Links

# Декоратор повтора соединения
def retry(timer):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f'INFO [{datetime.now()}]: Доступ заблокирован. Причина: {e}')
                    time.sleep(timer)
                    print(f'INFO [{datetime.now()}]: Повторная попытка')
        return wrapper
    return decorator


# Пути Xpath
xpth = dict(link_xpath=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-content"]/a[',                    #Получение сыслки на статью
            not_next_button=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-content"]/style',            #Проверка на отсутствие кнопки "Ещё"
            next_button=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-showMore-container"]/span',      #Кнопка "Ещё"
            news_exists=r'//*[@id="finfin-plugin-publication-list-list-next-compact"]',                                         #Проверка на наличие новостей на странице
            news_date=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-content"]/a[1]/div[1]/span[1]',    #Дата публикации
            text1=r'/html/body/div[1]/div[2]/div[2]/div/div[4]/div[1]/div[3]/div[1]',                                           #Текст публикации если есть график
            text2=r'/html/body/div[1]/div[2]/div[2]/div/div[4]/div[1]/div[3]/div[2]',                                           #Текст публикации если графика в новости нет
            date='//*[@id="publication-date"]',                                                                                 #Дата публикации статьи
            bonds_title=r'//*[@id="content-block"]/h2',                                                                         # Заголовок для сайтов bonds
            bonds_date=r'//*[@id="content-block"]/table[1]/tbody/tr/td/span',                                                   # Дата для сайтов bonds
            bonds_text=r'//*[@id="content-block"]/dl/dd')                                                                       # Текст для сайтов bonds


def check_exists_by_xpath(xpath):
    try:
        browser.find_element(By.XPATH, xpath)
        return True
    except (NoSuchElementException, InvalidSelectorException):
        return False

def check_exists_by_class_name(class_name):
    try:
        browser.find_element(By.CLASS_NAME, class_name)
        return True
    except (NoSuchElementException, InvalidSelectorException):
        return False

def db_insert(connection, abbr, link, title, text, date):
    with connection.cursor() as cursor:
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {abbr}_news (
                           item_id SERIAL,
                           date TIMESTAMP WITHOUT TIME ZONE,
                           title TEXT,
                           text TEXT,
                           link TEXT);
                           
                           INSERT INTO {abbr}_news (date, title, text, link)
                           VALUES ('{date}', '{title}', '{text}', '{link[8:]}');''')
        connection.commit()


@retry(600)
def get_article_data(link, browser):
    browser.get(link)
    time.sleep(2)
    if check_exists_by_class_name('error404-banner_text'):
        return (None, None, None)
    if check_exists_by_xpath('/html/body/div[1]/div[2]/div[1]/a') and browser.find_element(By.XPATH,
                                                                                           '/html/body/div[1]/div[2]/div[1]/a').text == 'Финансовый журнал':
        return (None, None, None)

    if link.startswith('https://bonds'):
        title = browser.find_element(By.XPATH, xpth['bonds_title']).text
        row_text = browser.find_elements(By.XPATH, xpth['bonds_text'])

        for i in row_text:
            tex = i.find_elements(By.TAG_NAME, 'p')
            text_new = ' '.join([i.text for i in tex]).strip()

        # изменяем триггер-символы кавычек в текстах
        table = str.maketrans({chr(39): chr(34), chr(8221): chr(34), chr(8220): chr(34)})
        text_new = text_new.translate(table)
        title = title.translate(table)
        date_news = browser.find_element(By.XPATH, xpth['bonds_date']).text.strip('[]')
        return title, text_new, date_news

    title = browser.find_element(By.CLASS_NAME, 'mb1x').text
    row_text = browser.find_elements(By.XPATH, xpth['text1'])

    for i in row_text:
        tex = i.find_elements(By.TAG_NAME, 'p')
        text_new = ' '.join([i.text for i in tex]).strip()

    # изменяем триггер-символы кавычек в текстах
    table = str.maketrans({chr(39): chr(34), chr(8221): chr(34), chr(8220): chr(34)})
    text_new = text_new.translate(table)
    title = title.translate(table)
    date_news = browser.find_element(By.XPATH, xpth['date']).text
    return title, text_new, date_news

def get_next_button(browser):
    while not check_exists_by_xpath(xpth['not_next_button']):
        show_more_btn = browser.find_element(By.XPATH, xpth['next_button'])
        browser.execute_script('arguments[0].click();', show_more_btn)
        time.sleep(2)

def get_link_list(browser):
    link_list = []
    content_counter = int(browser.find_element(By.XPATH, xpth['news_exists']).get_attribute('data-offset'))
    print(f'INFO [{datetime.now()}]: Для {abbr} было найдено {content_counter} новостей')
    for j in range(content_counter, 0, -1):
        link = browser.find_element(By.XPATH, xpth['link_xpath'] + str(j) + ']').get_attribute('href')
        link_list.append(link)
    return link_list

@retry(600)
def parse_process(browser, url, abbr):
    url += 'date/2014-01-01/2024-01-01/'
    browser.get(url)
    time.sleep(2)  # Ждём, чтобы прогрузилась страница

    # Нажать на кнопку "Показать еще" до тех пор, пока не появится заглушка
    get_next_button(browser)

    # Получение списка ссылок
    link_list = get_link_list(browser)

    global item_flag

    # Получение информации из ссылки
    for i in link_list:
        if i.startswith('https://bonds'):
            continue
        if item_flag:
            if i == 'https://www.finam.ru/publications/item/tatneft-vyplatit-dividendy-za-9-mesyatsev-v-razmere-3957-rublya-na-aktsiyu-20221227-1527/':
                item_flag = False
            else:
                continue
        title, text, date = get_article_data(i, browser)
        if (title, text, date) == (None, None, None):
            continue
        # Запись в базу данных
        db_insert(connection, abbr, i, title, text, date)

# Инициализация драйвера
browser = webdriver.Chrome()

abbr_flag = True
item_flag = False

for abbr, link in Links.news.items():
    if abbr_flag:
        if abbr == 'upro':
            abbr_flag = False
        else:
            continue
    parse_process(browser, link, abbr)
