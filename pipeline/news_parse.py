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
from datetime import date
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
                except Exception:
                    time.sleep(timer)
        return wrapper
    return decorator

# Пути Xpath
xpth = dict(link_xpath=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-content"]/a[', # Получение сыслки на статью
            not_next_button=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-content"]/style', # Проверка на отсутствие кнопки "Ещё"
            next_button=r'//*[@id="finfin-local-plugin-block-item-publication-list-filter-date-showMore-container"]/span', # Кнопка "Ещё"
            news_exists=r'//*[@id="finfin-plugin-publication-list-list-next-compact"]', # Проверка на наличие новостей на странице
            text1=r'//div[@data-id="text" and @class="mt2x p-margin font-xl"]', # Текст публикации
            date=r'//span[@data-id="date" and @class="mr1x"]', # Дата публикации статьи
            bonds_title=r'//*[@id="content-block"]/h2', # Заголовок для сайтов bonds
            bonds_date=r'//*[@id="content-block"]/table[1]/tbody/tr/td/span', # Дата для сайтов bonds
            bonds_text=r'//*[@id="content-block"]/dl/dd' # Текст для сайтов bonds
            )

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
        cursor.execute(f'''INSERT INTO {abbr}_news (date, title, text, link)
                           VALUES ('{date}', '{title}', '{text}', '{link[8:]}');''')
        connection.commit()

@retry(30)
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

@retry(30)
def get_link_list(browser):
    link_list = []
    if not check_exists_by_xpath(xpth['news_exists']):
        return link_list
    content_counter = int(browser.find_element(By.XPATH, xpth['news_exists']).get_attribute('data-offset'))
    for j in range(content_counter, 0, -1):
        link = browser.find_element(By.XPATH, xpth['link_xpath'] + str(j) + ']').get_attribute('href')
        link_list.append(link)
    return link_list

def parse_process(browser, url, abbr):
    url += f'date/{date.today()}/'
    browser.get(url)
    time.sleep(2)  # Ждём, чтобы прогрузилась страница

    # Нажать на кнопку "Показать еще" до тех пор, пока не появится заглушка
    get_next_button(browser)

    # Получение списка ссылок
    link_list = get_link_list(browser)

    # Получение информации из ссылки
    for i in link_list:
        title, text, date_news = get_article_data(i, browser)
        if (title, text, date_news) == (None, None, None):
            continue
        # Запись в базу данных
        db_insert(connection, abbr, i, title, text, date_news)
# Инициализация драйвера
browser = webdriver.Chrome()
for abbr, link in Links.news.items():
    parse_process(browser, link, abbr)
