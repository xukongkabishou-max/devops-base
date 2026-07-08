from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import time

# 定义一个简单的函数，作为任务
def print_current_time():
    print(f"当前时间是：{datetime.now()}")

def wait_task():
    print("等待5秒...")
    time.sleep(5)

def print_done():
    print("任务完成！")

# 定义 DAG 的默认参数
default_args = {
    'owner': 'airflow',                # DAG 的所有者名称
    'depends_on_past': False,          # 是否依赖上一个任务的状态
    'email_on_failure': False,         # 失败是否发送邮件
    'email_on_retry': False,           # 重试是否发送邮件
    'retries': 1,                      # 失败后重试的次数
    'retry_delay': timedelta(minutes=5) # 重试的间隔时间
}

# 定义 DAG
with DAG(
    'simple_dag',                      # DAG 名称
    default_args=default_args,         # 默认参数
    description='一个简单的 Airflow DAG 示例', # 描述
    schedule_interval=timedelta(days=1), # 调度间隔：每天运行一次
    start_date=datetime(2024, 1, 1),   # 开始日期
    catchup=False                      # 是否补齐错过的任务
) as dag:

    # 定义任务
    task1 = PythonOperator(
        task_id='print_current_time',  # 任务 ID
        python_callable=print_current_time # 调用的函数
    )

    task2 = PythonOperator(
        task_id='wait_5_seconds',     # 任务 ID
        python_callable=wait_task     # 调用的函数
    )

    task3 = PythonOperator(
        task_id='print_done',         # 任务 ID
        python_callable=print_done    # 调用的函数
    )

    # 定义任务依赖关系
    task1 >> task2 >> task3
