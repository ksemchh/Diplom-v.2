import psycopg2
from DataBase_config import host, user, password, db_name
from tqdm import tqdm
from Links import stocks

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# Функция обработки
def process2(text: str):
    list_text = text.split()
    list_text2 = list(filter(lambda x: all(list(map(lambda y: ord(y) not in range(65, 123), x))), list_text))
    return ' '.join(list_text2)

# Основная программа

abbr_flag = False

for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == 'trmk':
            abbr_flag = False
        else:
            continue
    with connection.cursor() as cursor:
        cursor.execute(f'''SELECT * FROM {abbr}_preprocess ORDER BY item_id;''')
        data = cursor.fetchall()


    for i in data:
        item_id, date, title, text, stock_bool, stock = i[0], i[1], i[2], i[3], i[4], i[5]
        if stock_bool is None:
            stock_bool = 'NULL'
        if stock is None:
            stock = 'NULL'
        title = process2(title)
        text = process2(text)
        with connection.cursor() as cursor:
            cursor.execute(
                f'''CREATE TABLE IF NOT EXISTS {abbr}_preprocess2 (
                    item_id SERIAL,
                    date TIMESTAMP WITHOUT TIME ZONE,
                    title TEXT,
                    text TEXT,
                    stock_bool BOOLEAN,
                    stock REAL);
                    INSERT INTO {abbr}_preprocess2 (date, title, text, stock_bool, stock)
                    VALUES ('{date}', '{title}', '{text}', {stock_bool}, {stock});'''
            )
    connection.commit()