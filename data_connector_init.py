import psycopg2
from DataBase_config import host, user, password, db_name
from tqdm import tqdm
from Links import stocks
from datetime import datetime, timedelta

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# Функция получения котировки после новости
def get_stock(cmp, date):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT change
                FROM {cmp}_stocks
                WHERE date = '{datetime.strftime(date + timedelta(days=1), '%Y-%m-%d')}';'''
        )
        stock = cursor.fetchone()
    if isinstance(stock, tuple):
        if stock[0] > 0:
            return True, stock[0]
        return False, stock[0]
    else:
        for i in range(1, 4):
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''SELECT change
                        FROM {cmp}_stocks
                        WHERE date = '{datetime.strftime(date + timedelta(days=i), '%Y-%m-%d')}';'''
                )
                stock = cursor.fetchone()
            if isinstance(stock, tuple):
                if stock[0] > 0:
                    return True, stock[0]
                return False, stock[0]
        return 'NULL', 'NULL'

# Основная программа
abbr_flag = False
for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == 'trmk':
            abbr_flag = False
        else:
            continue
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT date_trunc('day', date), array_agg(title), array_agg(text)
                FROM {abbr}_preproc
                GROUP BY date_trunc('day', date);'''
            )
        data = cursor.fetchall()

    for i in range(len(data)):
        date, title, text = data[i][0], ' '.join(data[i][1]), ' '.join(data[i][2])
        try:
            stock_bool, stock = get_stock(abbr, date)
        except IndexError:
            stock_bool, stock = 'NULL', 'NULL'
        with connection.cursor() as cursor:
            cursor.execute(
                f'''CREATE TABLE IF NOT EXISTS {abbr}_connected (
                           item_id SERIAL,
                           date TIMESTAMP WITHOUT TIME ZONE,
                           title TEXT,
                           text TEXT,
                           stock_bool BOOLEAN,
                           stock REAL);
                    INSERT INTO {abbr}_connected (date, title, text, stock_bool, stock)
                    VALUES ('{date}', '{title}', '{text}', {stock_bool}, {stock});'''
            )
        connection.commit()