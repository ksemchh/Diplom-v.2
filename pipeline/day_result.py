import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
from collections import namedtuple

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

day_result = dict()
for abbr, link in stocks.items():
    Params = namedtuple('Params', ['predict', 'change', 'direction'])
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT predict, change, direction
                FROM {abbr}_predicts
                WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP);'''
            )
        data = cursor.fetchall()
    if data:
        day_result[abbr] = Params(*data[0])

