from pymystem3 import Mystem
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
import string
from collections import Counter, OrderedDict

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

#Загрузка стоп-слов
with open('stopwords-ru.txt', 'r', encoding='utf-8') as file:
    stop_words = set(map(lambda x: x.strip(),file.readlines()))

# Функция обработки
def process(text):
    text_lower = text.lower() # Приведение к нижнему регистру
    text_punct = text_lower.translate(str.maketrans('', '', string.punctuation))  # Удаление пунктуации
    text_punct2 = text_punct.replace('«', '').replace('»', '')
    numbers = list(filter(lambda x: x.isalpha(), text_punct2.split()))
    eng_words = ' '.join(list(filter(lambda x: all(list(map(lambda y: ord(y) not in range(65, 123), x))), numbers))) # Удаление не кириллицы
    return eng_words

# Функция лемматизации
def lemma(text):
    m = Mystem()
    lemmas = m.lemmatize(text)
    result = ''.join(lemmas)
    return result

def filtering(text, word_counter, data_len):
    text_stop = list(filter(lambda x: x not in stop_words, text))  # Удаление стоп-слов
    repeats = list(OrderedDict.fromkeys(text_stop))  # Удаление повторящихся слов
    result = ' '.join(list(filter(lambda x: word_counter[x] > 5 and word_counter[x] < 0.9 * data_len , repeats)))
    return result

def checkExecTimeMystemOneText(texts):
    lol = lambda lst, sz: [lst[i:i+sz] for i in range(0, len(lst), sz)]
    txtpart = lol(texts, 1000)
    res = []
    for txtp in txtpart:
        alltexts = ' '.join([txt + ' br ' for txt in txtp])
        m = Mystem()
        words = m.lemmatize(alltexts)
        doc = []
        for txt in words:
            if txt != '\n' and txt.strip() != '':
                if txt == 'br':
                    res.append(doc)
                    doc = []
                else:
                    doc.append(txt)
    return res

# Основная программа

for abbr, link in stocks.items():
    # Получение новых новостей
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT date, title, text
                FROM {abbr}_news
                WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP)
                ORDER BY item_id;'''
            )
        current_data = cursor.fetchall()
    if not current_data:
        continue
    #Лемматизация новых новостей
    current_dates = list(map(lambda x: x[0], current_data))
    current_titles = checkExecTimeMystemOneText(list(map(lambda x: process(x[1]), current_data)))
    current_texts = checkExecTimeMystemOneText(list(map(lambda x: process(x[2]), current_data)))

    currnet_data = list(zip(current_dates, current_titles, current_texts))

    # Фильтрация на основе предыдущих данных
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT date, title, text
                FROM {abbr}_preproc
                ORDER BY item_id;'''
            )
        previous_data = cursor.fetchall()

    previous_dates = list(map(lambda x: x[0], previous_data))
    previous_titles = list(map(lambda x: process(x[1]), previous_data))
    previous_texts = list(map(lambda x: process(x[2]), previous_data))

    previous_data = list(zip(previous_dates, previous_titles, previous_texts))

    title_words_counter = Counter()
    text_words_counter = Counter()

    data_len = len(previous_data)

    for i in previous_data:
        date, title, text = i[0], i[1], i[2]
        title_words_counter += Counter(title)
        text_words_counter += Counter(text)

    data = list(map(lambda x: [x[0], filtering(x[1], title_words_counter, data_len),
                                   filtering(x[2], text_words_counter, data_len)], current_data))

    #Занесение новых записей в БД
    for i in data:
        date, title, text = i[0], i[1], i[2]
        with connection.cursor() as cursor:
            cursor.execute(
                f'''INSERT INTO {abbr}_preproc (date, title, text, text_len)
                    VALUES ('{date}', '{title}', '{text}', '{len(text)}');'''
            )
        connection.commit()