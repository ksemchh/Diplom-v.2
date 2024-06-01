import pandas as pd
import psycopg2
from DataBase_config import host, user, password, db_name
from datetime import datetime
from Links import stocks

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# Основная программа
for abbr, link in stocks.items():

    dfSentiment = pd.read_sql_query(f'''SELECT date, vector
                          FROM {abbr}_sentiment
                          WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP);''',
                       connection)

    dfSentimentToColumns = pd.DataFrame(dfSentiment['vector'].tolist(), columns=['neutral', 'positive', 'negative'])
    dfSentiment = pd.concat([dfSentiment, dfSentimentToColumns], axis=1)
    dfSentiment = dfSentiment.drop(columns=['vector'])

    dfStocks = pd.read_sql_query(f'''SELECT date, price, open, high, low, value, change
                          FROM {abbr}_stocks
                          WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP);''',
                       connection)
    dfStocks = dfStocks.iloc[::-1].reset_index(drop=True)

    dfMerged = pd.merge(dfStocks, dfSentiment, on='date', how='left')
    dfMerged = dfMerged.dropna(subset=['neutral'])
    dfMerged = dfMerged.drop(columns=['high', 'value', 'low', 'change'])

    for index, row in dfMerged.iterrows():
        with connection.cursor() as cursor:
            cursor.execute(
            f'''INSERT INTO {abbr}_feat (date, price, open, neutral, positive, negative)
            VALUES ('{datetime.strftime(row['date'], '%Y-%m-%d')}', {row['price']}, {row['open']}, {row['neutral']}, {row['positive']}, {row['negative']});''')
            connection.commit()