import psycopg2
from DataBase_config import host, user, password, db_name
from tqdm import tqdm
from Links import stocks
from collections import Counter

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# Функция обработки
def process3(text, words_counter):
    list_text = text.split()
    list_text2 = list(filter(lambda x: words_counter[x] >= 5 and words_counter[x] <= 1000, list_text))
    return ' '.join(list_text2)

# Основная программа

abbr_flag = False

for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == 'utar':
            abbr_flag = False
        else:
            continue

    words_counter = Counter()
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT title, text FROM {abbr}_preprocess2 ORDER BY item_id;''')
        words = cursor.fetchall()
    title_words = list(map(lambda x: x[0], words))
    text_words = list(map(lambda x: x[1], words))
    for i in title_words:
        words_counter += Counter(i.split())
    for i in text_words:
        words_counter += Counter(i.split())

    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM {abbr}_preprocess2 ORDER BY item_id;''')
        data = cursor.fetchall()

    for i in data:
        item_id, date, title, text, stock_bool, stock = i[0], i[1], i[2], i[3], i[4], i[5]
        if stock_bool is None:
            stock_bool = 'NULL'
        if stock is None:
            stock = 'NULL'

        title = process3(title, words_counter)
        text = process3(text, words_counter)
        with connection.cursor() as cursor:
            cursor.execute(
                f'''CREATE TABLE IF NOT EXISTS {abbr}_preprocess3 (
                    item_id SERIAL,
                    date TIMESTAMP WITHOUT TIME ZONE,
                    title TEXT,
                    text TEXT,
                    stock_bool BOOLEAN,
                    stock REAL);
                    INSERT INTO {abbr}_preprocess3 (date, title, text, stock_bool, stock)
                    VALUES ('{date}', '{title}', '{text}', {stock_bool}, {stock});'''
            )
    connection.commit()
