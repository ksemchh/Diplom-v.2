import psycopg2
from DataBase_config import host, user, password, db_name
from collections import OrderedDict
import torch
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
                WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP)
                ORDER BY item_id;'''
            )
        data = cursor.fetchall()

    if not data:
        return None

    dates = list(OrderedDict.fromkeys(list(map(lambda x: x[0].date(), data))))
    texts_dict = {j: [i[2] for i in data if i[0].date() == j] for j in dates}
    return texts_dict

def analyzeAndSaveSentiment(abbr):
    data = get_input_data(abbr)
    if not data:
        ...
    else:
        result = {}
        for date, headlines in data.items():
            averageScore = calculateDailySentiment(headlines)
            result[date] = averageScore

        for d, score in result.items():
            with connection.cursor() as cursor:
                cursor.execute(
                    f'''INSERT INTO {abbr}_sentiment (date, vector)
                    VALUES ('{d}', ARRAY{score});'''
            )
        connection.commit()

# Основная программа

for abbr, link in stocks.items():
    modelName = "blanchefort/rubert-base-cased-sentiment"
    tokenizer = AutoTokenizer.from_pretrained(modelName, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(modelName)
    analyzeAndSaveSentiment(abbr)