import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dropout, Dense, Activation
from keras.callbacks import ModelCheckpoint
from keras import regularizers
from keras import metrics
from keras.utils import plot_model
import matplotlib.pyplot as plt
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
from tqdm import tqdm
import os

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
abbr_flag = False
# abbr = 'alrs'
# for i in range(1):
for abbr, link in tqdm(stocks.items(), ncols=100):
    if abbr_flag:
        if abbr == '':
            ...
        else:
            continue
    os.mkdir(f'Models/{abbr}')
    df = pd.read_sql_query(f'''SELECT date, price, open, high, low, value, neutral, positive, negative
                          FROM {abbr}_feat;''',connection)

    features = df.drop(['date'], axis=1).values
    target = df['price'].values

    scalerFeatures = MinMaxScaler(feature_range=(0, 1))
    scalerTarget = MinMaxScaler(feature_range=(0, 1))

    featuresScaled = scalerFeatures.fit_transform(features)
    targetScaled = scalerTarget.fit_transform(target.reshape(-1, 1))

    lookBack = 3
    X, y = createDataset(featuresScaled, targetScaled, lookBack)

    trainSize = int(len(X) * 0.8)
    testSize = len(X) - trainSize

    trainX, testX = X[0:trainSize, :], X[trainSize:len(X), :]
    trainY, testY = y[0:trainSize], y[trainSize:len(y)]

    trainX = np.reshape(trainX, (trainX.shape[0], lookBack, trainX.shape[2]))
    testX = np.reshape(testX, (testX.shape[0], lookBack, testX.shape[2]))

    batchSize = 1
    epoch = 20
    neurons = 100
    dropout = 0.6

    model = Sequential()
    model.add(LSTM(neurons, return_sequences=True, activation='tanh', input_shape=(lookBack, features.shape[1])))
    model.add(Dropout(dropout))
    model.add(LSTM(neurons, return_sequences=True, activation='tanh'))
    model.add(Dropout(dropout))
    model.add(LSTM(neurons, activation='tanh'))
    model.add(Dropout(dropout))
    model.add(Dense(units=1, activation='linear', activity_regularizer=regularizers.l1(0.00001)))
    model.add(Activation('tanh'))

    plot_model(model, to_file=f'Models/{abbr}/Model plot.png', show_shapes=True, show_layer_names=True)

    model.compile(loss='mean_squared_error', optimizer='adam', metrics=[metrics.mean_squared_error, metrics.mean_absolute_error])

    model_save_path = f'Models/{abbr}/saved-model-{{epoch:02d}}.keras'
    checkpoint_callback = ModelCheckpoint(model_save_path,
                                          save_freq='epoch',
                                          verbose=0)

    history = model.fit(trainX, trainY, epochs=epoch, batch_size=batchSize, verbose=1, validation_split=0.2, callbacks=[checkpoint_callback])

    plt.figure(figsize=(15, 7.5))
    plt.plot(history.history['mean_squared_error'], label='Тренировочная MSE', marker='o')
    plt.plot(history.history['val_mean_squared_error'], label='Валидационная MSE', marker='o')
    plt.plot(history.history['mean_absolute_error'], label='Тренировачная MAE', marker='o')
    plt.plot(history.history['val_mean_absolute_error'], label='Валидационная MAE', marker='o')
    plt.legend()
    plt.grid(linestyle='--', linewidth=0.5)
    plt.xlim(-1, 20)
    plt.xticks(ticks=range(0,20), labels=range(1,21))
    plt.xlabel('Эпохи обучения')
    plt.title(f'Изменение метрик в зависимости от эпох обучения для компании {abbr}')
    plt.savefig(f'Models/{abbr}/Metrics plot', dpi=500, bbox_inches='tight')