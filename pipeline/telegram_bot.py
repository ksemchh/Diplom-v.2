import telebot
import psycopg2
from DataBase_config import host, user, password, db_name
from Links import stocks
import threading
import time
from datetime import date
import schedule

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name
        )

with open('telegram_token') as file:
    tok = file.read()

bot = telebot.TeleBot(tok)

def send_predict():
    result = dict()
    for abbr, link in stocks.items():
        with connection.cursor() as cursor:
            cursor.execute(f'''SELECT predict FROM {abbr}_predicts WHERE date_trunc('day', date) = date_trunc('day', CURRENT_TIMESTAMP)''')
            data = cursor.fetchone()[0]
        result[abbr] = data
    mess_text = f'По итогам сегодняшнего дня ({date.today()}) был составлен следющий прогноз:\n'
    for a, p in result.items():
        mess_text += f'<b>{a}</b> : {round(p, 2)} ₽\n'

    bot.send_message(chat_id=1716499244, text=mess_text, parse_mode='html')

def foo():
    schedule.every().day.at("23:30").do(send_predict)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=foo).start()
    bot.polling(none_stop=True, interval=0)