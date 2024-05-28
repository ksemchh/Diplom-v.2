import matplotlib.pyplot as plt
from wordcloud import WordCloud
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
import numpy as np
import pandas as pd
import random


connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

# x = sorted(stocks.keys())
# y = []
# news_count = 0
# for i in x:
#         with connection.cursor() as cursor:
#                 cursor.execute(
#                 f'''SELECT count(*)
#                 FROM {i}_stocks;'''
#                 )
#                 data = cursor.fetchone()[0]
#         news_count += data
#         y.append(data)
# data = zip(x, y)
# df = pd.DataFrame(data, columns=['company', 'count'])
#
#
# plt.figure(figsize=(13, 6.5))
# plt.bar(df['company'], df['count'], color='lightblue', width=.8)
# for i, val in enumerate(df['count'].values):
#         if val < 2300:
#             plt.text(i, val, val, horizontalalignment='center', verticalalignment='bottom', fontdict={'fontweight': 500, 'size': 8})
# plt.xlabel('Аббревиатура компании')
# plt.ylabel('Количество записей котировок')
# plt.xticks(rotation=60)
# plt.yticks(ticks=np.arange(0, 2700, step=250), minor=True)
# plt.ylim(0, 2700)
# plt.title("Распределение количества записей котировок по компаниям", fontsize=14)
# plt.show()
# print(news_count)


with connection.cursor() as cursor:
        cursor.execute(
                f'''SELECT date_trunc('day', date), array_agg(text)
                FROM alrs_preproc
                GROUP BY date_trunc('day', date);''')
        data = cursor.fetchall()
with connection.cursor() as cursor:
        cursor.execute(
                f'''SELECT date, neutral, positive, negative
                FROM alrs_feat;''')
        setiment = cursor.fetchall()
data = list(map(lambda x: [x[0], ' '.join(x[1])], data))
dfText = pd.DataFrame(data, columns=['date', 'text'])

dfSent = pd.DataFrame(setiment, columns=['date', 'neutral', 'positive', 'negative'])
dfSent['date'] = dfSent['date'].astype('datetime64[ns]')

dfMerged = pd.merge(dfText, dfSent, on='date', how='left')
dfMerged = dfMerged.dropna(subset=['neutral'])

#POSISTIVE

dfPositive = dfMerged.query('positive > 0.5')
print(dfPositive.describe())
texts = ' '.join(dfPositive['text'].values)

wordcloud = WordCloud(width=1920, height=1080, random_state=1, background_color='white').generate(texts)
plt.figure()
plt.axis('off')
plt.title("WordCloud для позитивных новостей", fontsize=14)
plt.imshow(wordcloud)
plt.show()

#NEGATIVE

dfPositive = dfMerged.query('negative > 0.5')
print(dfPositive.describe())
texts = ' '.join(dfPositive['text'].values)

wordcloud = WordCloud(width=1920, height=1080, random_state=1, background_color='white').generate(texts)
plt.figure()
plt.axis('off')
plt.title("WordCloud для негативных новостей", fontsize=14)
plt.imshow(wordcloud)
plt.show()

#NEUTRAL

dfPositive = dfMerged.query('neutral > 0.5')
print(dfPositive.describe())
texts = ' '.join(dfPositive['text'].values)

wordcloud = WordCloud(width=1920, height=1080, random_state=1, background_color='white').generate(texts)
plt.figure()
plt.axis('off')
plt.title("WordCloud для нейтральных новостей", fontsize=14)
plt.imshow(wordcloud)
plt.show()









