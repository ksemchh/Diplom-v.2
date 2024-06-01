import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks


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

# основная программа

df = pd.read_sql_query(f'''SELECT date, price, open, neutral, positive, negative
                      FROM afks_feat;''', connection)

features = df.drop(['date', 'price'], axis=1).values
target = df['price'].values

scalerFeatures = MinMaxScaler(feature_range=(0, 1))
scalerTarget = MinMaxScaler(feature_range=(0, 1))

featuresScaled = scalerFeatures.fit_transform(features)
targetScaled = scalerTarget.fit_transform(target.reshape(-1, 1))

lookBack = 3
X = featuresScaled[:3]

X = np.reshape(X, (1, lookBack, 4))

model = load_model(f'Models/afks/best_model.keras')

Predict = model.predict(X)
print(Predict)

PredictInv = scalerTarget.inverse_transform(Predict)

print(PredictInv)