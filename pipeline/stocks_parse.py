import psycopg2
from DataBase_config import host, password, db_name, user
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from Links import stocks

# подключение к базе данных
connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name)

def number(num, mode):
    if mode == 1:
        return float(num.replace('.','').replace(',', '.'))
    elif mode == 2:
        if num[-1] == 'K':
            return float(num[:-1].replace(',', '.')) * 1000
        elif num[-1] == 'M':
            return float(num[:-1].replace(',', '.')) * 1000000
        elif num[-1] == 'B':
            return float(num[:-1].replace(',', '.')) * 1000000000
    elif mode == 3:
        return float(num[:-1])

# Получение котировок
def get_currencies(browser, url, abbr):
    while True:
        try:
            # Opening the connection and grabbing the page
            browser.get(url)
            # Getting the tables on the page and quiting
            data = browser.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/table/tbody').text.split('\n')
            s = data[0].split(' ')

            with connection.cursor() as cursor:
                cursor.execute(
                    f'''SELECT date
                        FROM {abbr}_stocks
                        WHERE item_id = (SELECT MAX(item_id) FROM {abbr}_stocks);'''
                )
                last_date = cursor.fetchone()[0]

            if last_date == s[0]:
                break

            if len(s) == 7:
                with connection.cursor() as cursor:
                    cursor.execute(
                    f'''INSERT INTO {abbr}_stocks (date, price, open, high, low, value, change)
                    VALUES ('{s[0]}', '{number(s[1], 1)}', '{number(s[2], 1)}',
                    '{number(s[3], 1)}', '{number(s[4], 1)}',
                    '{number(s[5], 2)}', '{number(s[6], 3)}');'''
                    )
                    connection.commit()
            if len(s) == 6:
                with connection.cursor() as cursor:
                    cursor.execute(
                    f'''INSERT INTO {abbr}_stocks (date, price, open, high, low, change)
                    VALUES ('{s[0]}', '{number(s[1], 1)}', '{number(s[2], 1)}',
                    '{number(s[3], 1)}', '{number(s[4], 1)}',
                    '{number(s[5], 3)}');'''
                    )
                    connection.commit()
            break
        except:
            browser.quit()
            sleep(30)
            browser = webdriver.Chrome()
            continue


for abbr, link in stocks.items():
    # Создание объекта браузера
    browser = webdriver.Chrome()
    get_currencies(browser, link, abbr)

