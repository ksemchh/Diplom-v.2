from pymystem3 import Mystem
import psycopg2
from DataBase_config import host, user, password, db_name
from tqdm import tqdm
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
abbr_flag = False
# abbr = 'rosn'
# for i in range(1):
for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == 'rosn':
            ...
        else:
            continue
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT date, title, text
                FROM {abbr}_news
                ORDER BY item_id;'''
            )
        data = cursor.fetchall()

    dates = list(map(lambda x: x[0], data))
    titles = checkExecTimeMystemOneText(list(map(lambda x: process(x[1]), data)))
    texts = checkExecTimeMystemOneText(list(map(lambda x: process(x[2]), data)))

    data = list(zip(dates, titles, texts))

    title_words_counter = Counter()
    text_words_counter = Counter()

    data_len = len(data)

    for i in data:
        date, title, text = i[0], i[1], i[2]
        title_words_counter += Counter(title)
        text_words_counter += Counter(text)

    data = list(map(lambda x: [x[0], filtering(x[1], title_words_counter, data_len),
                                   filtering(x[2], text_words_counter, data_len)], data))

    for i in data:
        date, title, text = i[0], i[1], i[2]

        with connection.cursor() as cursor:
            cursor.execute(
                f'''CREATE TABLE IF NOT EXISTS {abbr}_preproc (
                           item_id SERIAL,
                           date TIMESTAMP WITHOUT TIME ZONE,
                           title TEXT,
                           text TEXT,
                           text_len REAL);
                    INSERT INTO {abbr}_preproc (date, title, text, text_len)
                    VALUES ('{date}', '{title}', '{text}', '{len(text)}');'''
            )
        connection.commit()