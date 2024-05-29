import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dropout, Dense, Activation
from keras.models import load_model
from keras.callbacks import ModelCheckpoint
from keras import regularizers
from keras import metrics
from keras.utils import plot_model
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, accuracy_score
import matplotlib.pyplot as plt
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
from tqdm import tqdm
import os
pd.set_option('display.max_columns', None)

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
abbr_flag = True
abbr = 'alrs'
for i in range(1):
# for abbr, link in tqdm(stocks.items(), ncols=100):
#     if abbr_flag:
#         if abbr == 'qiwidr':
#             ...
#         else:
#             continue
    # os.mkdir(f'Models/{abbr}')
    df = pd.read_sql_query(f'''SELECT date, price, open, neutral, positive, negative
                          FROM {abbr}_feat;''',connection)

    features = df.drop(['date', 'price'], axis=1).values
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

    # batchSize = 1
    # epoch = 20
    # neurons = 100
    # dropout = 0.6
    #
    # model = Sequential()
    # model.add(LSTM(neurons, return_sequences=True, activation='tanh', input_shape=(lookBack, features.shape[1])))
    # model.add(Dropout(dropout))
    # model.add(LSTM(neurons, return_sequences=True, activation='tanh'))
    # model.add(Dropout(dropout))
    # model.add(LSTM(neurons, activation='tanh'))
    # model.add(Dropout(dropout))
    # model.add(Dense(units=1, activation='linear', activity_regularizer=regularizers.l1(0.00001)))
    # model.add(Activation('tanh'))
    #
    # plot_model(model, to_file=f'Models/{abbr}/Model plot.png', show_shapes=True, show_layer_names=True)
    #
    # model.compile(loss='mean_squared_error', optimizer='adam', metrics=[metrics.mean_squared_error, metrics.mean_absolute_error])
    #
    # model_save_path = f'Models/{abbr}/saved-model-{{epoch:02d}}.keras'
    # checkpoint_callback = ModelCheckpoint(model_save_path,
    #                                       save_freq='epoch',
    #                                       verbose=0)
    #
    # history = model.fit(trainX, trainY, epochs=epoch, batch_size=batchSize, verbose=1, validation_split=0.2, callbacks=[checkpoint_callback])
    #
    # plt.figure(figsize=(15, 7.5))
    # plt.plot(history.history['mean_squared_error'], label='Train MSE')
    # plt.plot(history.history['val_mean_squared_error'], label='Validation MSE')
    # plt.plot(history.history['mean_absolute_error'], label='Train MAE')
    # plt.plot(history.history['val_mean_absolute_error'], label='Validation MAE')
    # plt.legend()
    # plt.savefig(f'Models/{abbr}/Metrics plot', dpi=500, bbox_inches='tight')

    # model.save(f'Models/{abbr}/best_model.keras')
    model = load_model(f'Models/{abbr}/best_model.keras')

    trainPredict = model.predict(trainX)
    testPredict = model.predict(testX)

    trainPredictInv = scalerTarget.inverse_transform(trainPredict)
    trainYInv = scalerTarget.inverse_transform(np.reshape(trainY, (trainY.shape[0], 1)))

    testPredictInv = scalerTarget.inverse_transform(testPredict)
    testYInv = scalerTarget.inverse_transform(np.reshape(testY, (testY.shape[0], 1)))

    trainPredictInv1 = list(map(lambda x: float(*x), trainPredictInv))
    dfTrainPredictInv = pd.DataFrame(trainPredictInv1, columns=['predict'])
    dfTrainPredictInv['date'] = df['date'][lookBack:len(trainPredictInv) + lookBack].values
    dfTrain = pd.merge(df, dfTrainPredictInv, how='left', on='date')
    dfTrain = dfTrain.dropna(subset='predict')
    dfTrain['change'] = dfTrain['price'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTrain['direction'] = dfTrain['change'] > 0
    dfTrain['predictChange'] = dfTrain['predict'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTrain['predictDirection'] = dfTrain['predictChange'] > 0
    print(dfTrain.head(30))


    testPredictInv1 = list(map(lambda x: float(*x), testPredictInv))
    dfTestPredictInv = pd.DataFrame(testPredictInv1, columns=['predict'])
    dfTestPredictInv['date'] = df['date'][len(trainPredictInv) + lookBack:].values
    dfTest = pd.merge(df, dfTestPredictInv, how='left', on='date')
    dfTest = dfTest.dropna(subset='predict')
    dfTest['change'] = dfTest['price'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTest['direction'] = dfTest['change'] > 0
    dfTest['predictChange'] = dfTest['predict'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTest['predictDirection'] = dfTest['predictChange'] > 0
    print(dfTest.head(30))

    trainMSE = mean_squared_error(dfTrain['price'], dfTrain['predict'])
    print(f'trainMSE: {trainMSE}')
    testMSE = mean_squared_error(dfTest['price'], dfTest['predict'])
    print(f'testMSE: {testMSE}')

    trainRMSE = np.sqrt(mean_squared_error(dfTrain['price'], dfTrain['predict']))
    print(f'trainRMSE: {trainRMSE}')
    testRMSE = np.sqrt(mean_squared_error(dfTest['price'], dfTest['predict']))
    print(f'testRMSE: {testRMSE}')

    trainMAE = mean_absolute_error(dfTrain['price'], dfTrain['predict'])
    print(f'trainMAE: {trainMAE}')
    testMAE = mean_absolute_error(dfTest['price'], dfTest['predict'])
    print(f'testMAE: {testMAE}')

    trainMAPE = mean_absolute_percentage_error(dfTrain['price'], dfTrain['predict'])
    print(f'trainMAPE: {trainMAPE}')
    testMAPE = mean_absolute_percentage_error(dfTest['price'], dfTest['predict'])
    print(f'testMAPE: {testMAPE}')

    trainAccuracy = accuracy_score(dfTrain['direction'], dfTrain['predictDirection'])
    print(f'trainAccuracy: {trainAccuracy}')
    testAccuracy = accuracy_score(dfTest['direction'], dfTest['predictDirection'])
    print(f'testAccuracy: {testAccuracy}')
    #
    # with open(f'Models/{abbr}/model_description.txt', mode='w', encoding='utf-8') as file:
    #     print('Model Summary:', file=file)
    #     print(model.summary(), file=file)
    #     print('Predict table:', file=file)
    #     print(dfTrain.head(), file=file)
    #     print(f'Training MSE: {trainMSE}', file=file)
    #     print(f'Testing MSE: {testMSE}', file=file)
    #     print(f'Training RMSE: {trainRMSE}', file=file)
    #     print(f'Testing RMSE: {testRMSE}', file=file)
    #     print(f'Training MAE: {trainMAE}', file=file)
    #     print(f'Testing MAE: {testMAE}', file=file)
    #     print(f'Training MAPE: {trainMAPE}', file=file)
    #     print(f'Testing MAPE: {testMAPE}', file=file)
    #
    # dates = df['date'].values[lookBack:]
    # sampleInterval = 50
    # sampledDates = dates[::sampleInterval]
    #
    # plt.figure(figsize=(20, 10))
    # plt.plot(dfTrain['date'], dfTrain['price'], label='Actual Train')
    # plt.plot(dfTrain['date'], dfTrain['predict'], label='Predicted Train')
    # plt.plot(dfTest['date'], dfTest['price'], label='Actual Test')
    # plt.plot(dfTest['date'], dfTest['predict'], label='Predicted Test')
    # plt.xticks(sampledDates, rotation=90)
    # plt.legend()
    # plt.savefig(f'Models/{abbr}/Train result plot', dpi=500, bbox_inches='tight')