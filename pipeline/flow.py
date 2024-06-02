from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.telegram.operators.telegram import TelegramOperator
from airflow.utils.trigger_rule import TriggerRule

with open('telegram_token') as file:
    tok = file.read()
chat_id = 1716499244

send_telegram_message = TelegramOperator(
    task_id="send_telegram_message",
    token=tok,
    chat_id=chat_id,
    text="Расчет прогноза выполнен.")

with DAG(
    "daily_effectiveness", # Идентификатор, отобразится в консоли
    default_args={
        "depends_on_past": False, # Зависимость задач от предыдущих
        "retries": 1, # Число перепопыток в случае неудаче
        "retry_delay": timedelta(seconds=30)}, # Интервал между попытками
    description="Предсказание цен на акции",
    schedule_interval='@daily', # Ежедневное исполнение
    start_date=datetime(2024, 6, 5, 23, 0), # Когда начать исполнение по расписанию
    catchup=False,
    tags=["Диплом", "Prediction", "Акции"],) as dag:


    t1 = BashOperator(
     task_id="entering_virtual_environment", # Идентификатор таски для отслеживания в консоли
     bash_command="source airflow_env/bin/activate", retries=2)

    t2 = BashOperator(
      task_id="news_parsing",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t3 = BashOperator(
      task_id="text_preprocessing",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t4 = BashOperator(
      task_id="sentiment_analyze",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t5 = BashOperator(
      task_id="stocks_parsing",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t6 = BashOperator(
      task_id="data_preparing",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t7 = BashOperator(
      task_id="predicting",
      depends_on_past=False,
      bash_command="python3 /home/fitwist/airflow/df-to-looker/dialogflow-to-bigquery.py",
      retries=2)

    t1 >> t5 >> t6 >> t7
    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> TelegramOperator(
    task_id="send_telegram_message",
    token=tok,
    chat_id=chat_id,
    trigger_rule=TriggerRule.ONE_FAILED,
    text="Оодна из ежедневных тасков не выполнена. Проверь логи.")