import pandas as pd
import psycopg2
from DataBase_config import host, user, password, db_name
from datetime import datetime
from Links import stocks
from tqdm import tqdm

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# основная программа
abbr_flag = False
# abbr = 'rosn'
# for i in range(1):
for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == 'rosn':
            ...
        else:
            continue
    dfSentiment = pd.read_sql_query(f'''SELECT date, vector
                          FROM {abbr}_sentiment;''',
                       connection)

    dfSentimentToColumns = pd.DataFrame(dfSentiment['vector'].tolist(), columns=['neutral', 'positive', 'negative'])
    dfSentiment = pd.concat([dfSentiment, dfSentimentToColumns], axis=1)
    dfSentiment = dfSentiment.drop(columns=['vector'])

    dfStocks = pd.read_sql_query(f'''SELECT date, price, open, high, low, value, change
                          FROM {abbr}_stocks;''',
                       connection)
    dfStocks = dfStocks.iloc[::-1].reset_index(drop=True)

    dfMerged = pd.merge(dfStocks, dfSentiment, on='date', how='left')
    dfMerged = dfMerged.dropna(subset=['neutral', 'value'])
    dfMerged = dfMerged.drop(columns=['change'])

    with connection.cursor() as cursor:
        cursor.execute(
        f'''CREATE TABLE IF NOT EXISTS {abbr}_feat (
                   item_id SERIAL,
                   date DATE,
                   price REAL,
                   open REAL,
                   high REAL,
                   low REAL,
                   value REAL,
                   neutral REAL,
                   positive REAL,
                   negative REAL);'''
        )
        connection.commit()

    for index, row in dfMerged.iterrows():
        with connection.cursor() as cursor:
            cursor.execute(
            f'''INSERT INTO {abbr}_feat (date, price, open, high, low, value, neutral, positive, negative)
            VALUES ('{datetime.strftime(row['date'], '%Y-%m-%d')}',
                    {row['price']},
                    {row['open']},
                    {row['high']},
                    {row['low']},
                    {row['value']},
                    {row['neutral']},
                    {row['positive']},
                    {row['negative']});''')
            connection.commit()