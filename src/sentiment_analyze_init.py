import psycopg2
from DataBase_config import host, user, password, db_name
from collections import OrderedDict
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from Links import stocks


connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )
def calculateDailySentiment(headlines):
    inputs = tokenizer(headlines, return_tensors="pt", truncation=True, padding=True, max_length=512, return_attention_mask=True)
    outputs = model(**inputs)
    logits = outputs.logits
    scores = logits.softmax(dim=1)
    averageScore = scores.mean(dim=0).tolist()
    return averageScore

def get_input_data(abbr):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT date, title, text
                FROM {abbr}_preproc
                ORDER BY item_id;'''
            )
        data = cursor.fetchall()

    dates = list(OrderedDict.fromkeys(list(map(lambda x: x[0].date(), data))))

    texts_dict = {j: [i[2] for i in data if i[0].date() == j] for j in dates}
    return texts_dict

def analyzeAndSaveSentiment(abbr):
    data = get_input_data(abbr)

    result = {}

    for date, headlines in data.items():
        averageScore = calculateDailySentiment(headlines)
        result[date] = averageScore


    with connection.cursor() as cursor:
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS {abbr}_sentiment (
                       item_id SERIAL,
                       date TIMESTAMP WITHOUT TIME ZONE,
                       vector REAL[]);'''
        )
        connection.commit()

    for d, score in result.items():
        with connection.cursor() as cursor:
            cursor.execute(
                f'''INSERT INTO {abbr}_sentiment (date, vector)
                VALUES ('{d}', ARRAY{score});'''
        )
    connection.commit()

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
    modelName = "blanchefort/rubert-base-cased-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(modelName, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(modelName)
    analyzeAndSaveSentiment(abbr)