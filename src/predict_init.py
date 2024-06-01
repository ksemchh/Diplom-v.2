import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, accuracy_score
import matplotlib.pyplot as plt
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
from tqdm import tqdm
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

def myprint(s):
    with open(f'Models/{abbr}/model_description.txt', mode='w', encoding='utf-8') as file:
        print(s, file=file)

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

    testPredictInv1 = list(map(lambda x: float(*x), testPredictInv))
    dfTestPredictInv = pd.DataFrame(testPredictInv1, columns=['predict'])
    dfTestPredictInv['date'] = df['date'][len(trainPredictInv) + lookBack:].values
    dfTest = pd.merge(df, dfTestPredictInv, how='left', on='date')
    dfTest = dfTest.dropna(subset='predict')
    dfTest['change'] = dfTest['price'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTest['direction'] = dfTest['change'] > 0
    dfTest['predictChange'] = dfTest['predict'].rolling(2, min_periods=2).apply(lambda x: (x.iat[-1] / x.iat[-2]) * 100 - 100)
    dfTest['predictDirection'] = dfTest['predictChange'] > 0

    trainMSE = mean_squared_error(dfTrain['price'], dfTrain['predict'])
    testMSE = mean_squared_error(dfTest['price'], dfTest['predict'])

    trainRMSE = np.sqrt(mean_squared_error(dfTrain['price'], dfTrain['predict']))
    testRMSE = np.sqrt(mean_squared_error(dfTest['price'], dfTest['predict']))

    trainMAE = mean_absolute_error(dfTrain['price'], dfTrain['predict'])
    testMAE = mean_absolute_error(dfTest['price'], dfTest['predict'])

    trainMAPE = mean_absolute_percentage_error(dfTrain['price'], dfTrain['predict'])
    testMAPE = mean_absolute_percentage_error(dfTest['price'], dfTest['predict'])

    trainAccuracy = accuracy_score(dfTrain['direction'], dfTrain['predictDirection'])
    testAccuracy = accuracy_score(dfTest['direction'], dfTest['predictDirection'])

    with open(f'Models/{abbr}/model_description.txt', mode='a', encoding='utf-8') as file:
        print('Model Summary:', file=file)
        model.summary(print_fn=myprint)
        print('Predict table:', file=file)
        print(dfTrain.head(10), file=file)
        print(f'Training MSE: {trainMSE}', file=file)
        print(f'Testing MSE: {testMSE}', file=file)
        print(f'Training RMSE: {trainRMSE}', file=file)
        print(f'Testing RMSE: {testRMSE}', file=file)
        print(f'Training MAE: {trainMAE}', file=file)
        print(f'Testing MAE: {testMAE}', file=file)
        print(f'Training MAPE: {trainMAPE}', file=file)
        print(f'Testing MAPE: {testMAPE}', file=file)
        print(f'Training Accuracy: {trainAccuracy}', file=file)
        print(f'Testing Accuracy: {testAccuracy}', file=file)

    dates1 = df['date'].values[lookBack:]
    sampleInterval1 = 50
    sampledDates1 = dates1[::sampleInterval1]

    dates2= dfTest['date'].values
    sampleInterval2 = 10
    sampledDates2 = dates2[::sampleInterval2]


    plt.figure(figsize=(20, 10))
    plt.plot(dfTrain['date'], dfTrain['price'], label='Фактическое тренировочное значение цены')
    plt.plot(dfTrain['date'], dfTrain['predict'], label='Предсказанное тренировочное значение цены')
    plt.plot(dfTest['date'], dfTest['price'], label='Фактическое тестовое значение цены')
    plt.plot(dfTest['date'], dfTest['predict'], label='Предсказанное тестовое значение цены')
    plt.xticks(sampledDates1, rotation=90)
    plt.xlabel('Даты выхода новостей')
    plt.ylabel('Цена акции')
    plt.title(f'Сводный график фактических и предсказанных цен для компании {abbr}')
    plt.grid(linestyle='--', linewidth=0.5)
    plt.legend()
    plt.savefig(f'Models/{abbr}/Test-Train result plot', dpi=500, bbox_inches='tight')

    plt.figure(figsize=(20, 10))
    plt.plot(dfTest['date'], dfTest['price'], label='Фактическое значение цены', color='green')
    plt.plot(dfTest['date'], dfTest['predict'], label='Предсказанное значение цены', color='red')
    plt.xticks(sampledDates2, rotation=90)
    plt.xlabel('Даты выхода новостей')
    plt.ylabel('Цена акции')
    plt.title(f'График тестовых значений фактических и предсказанных цен для компании {abbr}')
    plt.grid(linestyle='--', linewidth=0.5)
    plt.legend()
    plt.savefig(f'Models/{abbr}/Test result plot', dpi=500, bbox_inches='tight')