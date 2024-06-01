import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
from datetime import datetime, date

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

def createDataset(dataset, target, lookBack=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - lookBack):
        a = dataset[i:(i + lookBack), :]
        dataX.append(a)
        dataY.append(target[i + lookBack])
    return np.array(dataX), np.array(dataY)

def myprint(s):
    with open(f'Models/{abbr}/model_description.txt', mode='w', encoding='utf-8') as file:
        print(s, file=file)

# основная программа
for abbr, link in stocks.items():
    df = pd.read_sql_query(f'''SELECT date, price, open, neutral, positive, negative
                          FROM {abbr}_feat;''', connection)

    if df.values[-1][0] == date.today():
        continue

    features = df.drop(['date', 'price'], axis=1).values
    target = df['price'].values

    scalerFeatures = MinMaxScaler(feature_range=(0, 1))
    scalerTarget = MinMaxScaler(feature_range=(0, 1))

    featuresScaled = scalerFeatures.fit_transform(features)
    targetScaled = scalerTarget.fit_transform(target.reshape(-1, 1))

    lookBack = 3
    X = np.reshape(featuresScaled[-lookBack:], (1, lookBack, 4))
    model = load_model(f'Models/{abbr}/best_model.keras')

    Predict = model.predict(X)
    PredictInv = scalerTarget.inverse_transform(Predict)[0][0]

    change = 100 * PredictInv/df.values[-1][1]
    direction = change > 0

    with connection.cursor() as cursor:
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS {abbr}_prdicts (
                        item_id SERIAL,
                        date DATE,
                        predict REAL,
                        change REAL,
                        direction BOOL);
                INSERT INTO {abbr}_prdicts (date, predict)
                VALUES ('{datetime.now().strftime("%Y-%M-%d")}', '{PredictInv}', {change}, {direction});'''
        )
    connection.commit()

