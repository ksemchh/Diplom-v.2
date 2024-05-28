TF_ENABLE_ONEDNN_OPTS=0
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Dense, LSTM, GRU, Dropout, Activation, Conv1D, MaxPooling1D
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.metrics import AUC
from keras.optimizers import Adam
from keras.regularizers import l1_l2
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras import utils
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
from DataBase_config import host, user, password, db_name
import math

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name)

num_words = 5000

df = pd.read_sql_query('''SELECT text, stock_bool
                          FROM sber_connected
                          WHERE stock_bool IS NOT NULL;''', connection)

# with connection.cursor() as cursor:
#     cursor.execute(
#         f'''SELECT AVG(text_len)
#             FROM sber_preproc;'''
#     )
#     num_words = math.ceil(cursor.fetchone()[0])


lemmas = df['text']
news_count = len(lemmas)
border = int(news_count * 0.75)

training_y = df['stock_bool'].astype(int)

tokenizer = Tokenizer(num_words=num_words)
tokenizer.fit_on_texts(lemmas)
sequnces = tokenizer.texts_to_sequences(lemmas)

total_news = pad_sequences(sequnces)
training_X = total_news


dropout_rate = 0.5
dimension = 64
l1_rate = 0.1
l2_rate = 0.1
l_rate = 0.01
batch_size = 32
epochs = 32
validation_split = 0.2
path = 'C:\\Users\\Дом\\PycharmProjects\\Diplom v.2'
sep = '\\'

model_save_path = 'best_model_sber_stock.keras'
checkpoint_callback = ModelCheckpoint(model_save_path,
                                      monitor='val_accuracy',
                                      save_best_only=True,
                                      verbose=1)

max_review_length = 800
top_words = 10000
embedding_vecor_length = 32
model = Sequential()
model.add(Embedding(top_words, embedding_vecor_length, input_length=max_review_length))
model.add(Conv1D(filters=32, kernel_size=3, padding='same', activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(LSTM(100))
model.add(Dense(1, activation='sigmoid'))
optimizer = Adam(learning_rate=0.001)
model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

hist = model.fit(training_X, training_y, batch_size=batch_size, epochs=epochs, validation_split=validation_split, callbacks=[checkpoint_callback])

with open(path + sep + 'sber_history.txt', 'w+', encoding='utf8') as temp:
    temp.write(str(hist.history))

plt.plot(hist.history['accuracy'], label='Доля верных ответов на обучающем наборе')
plt.plot(hist.history['val_accuracy'], label='Доля верных ответов на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.legend()
plt.show()

plt.plot(hist.history['precision'], label='Доля верных ответов в пределах класса на обучающем наборе')
plt.plot(hist.history['val_precision'], label='Доля верных ответов в пределах класса на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.legend()
plt.show()

plt.plot(hist.history['recall'], label='Доля истинно положительных классификаций на обучающем наборе')
plt.plot(hist.history['val_recall'], label='Доля истинно положительных классификаций на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.legend()
plt.show()

plt.plot(hist.history['AUC'], label='Метрика оценки качества процесса классификации на обучающем наборе')
plt.plot(hist.history['val_AUC'], label='Метрика оценки качества процесса классификации на проверочном наборе')
plt.xlabel('Эпоха обучения')
plt.ylabel('Доля верных ответов')
plt.legend()
plt.show()