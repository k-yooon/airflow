from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.hooks.mysql_hook import MySqlHook
from airflow.models import Variable

from common.tool.YamlUtil import open_yaml
from datetime import datetime
import common.constant.Global
import common.entity.Context

import pendulum
import json
import ast
import os
import pandas as pd

const = common.constant.Global.GlobalConstant()

local_tz = pendulum.timezone("Asia/Seoul")
# alert = SlackAlert(const.SLACK_CHANNEL_PROD)
home_path = os.path.expanduser("~")

mysql_hook = MySqlHook(mysql_conn_id = 'test', schema = 'test')
connection = mysql_hook.get_conn()
cursor = connection.cursor()

args = {
    "owner": "kyoon lee",
    "depends_on_past": False,
    "start_date": datetime(2022, 12, 10, tzinfo=local_tz)
}

@dag(
    default_args=args,
    description="",
    schedule_interval="@daily",
    catchup=False,
    concurrency=4,
    doc_md="""
            DB 결과를 이용해 dynamic task 생성하기
    """
)
def example_dynamic_task_with_db_data():
    dag_id = "{{ dag.dag_id }}"

    def get_target_data(**context):
        query = "select id from example"

        cursor.execute(query)
        rows = cursor.fetchall()
        Variable.set(key='id_list', value=list(rows), serialize_json=False)

        return None

    get_target_data = PythonOperator(
        task_id="get_target_data",
        python_callable=get_target_data
    )

    with TaskGroup('transform_data_group', prefix_group_id=False,) as transform_data_group:
        id_list = Variable.get('id_list', default_var=['default'], deserialize_json=False)

        for id in ast.literal_eval(id_list):

            operator1 = PythonOperator(
                task_id=f"task1_{id}",
                python_callable=ex_func1
            )

            operator2 = PythonOperator(
                task_id=f"task2_{id}",
                python_callable=ex_func2
            )

            operator1 >> operator2


    load_data = PythonOperator(
        task_id=f"load_data",
        python_callable=ex_func3
    )

    get_target_data >> transform_data_group >> load_data

dag = example_dynamic_task_with_db_data()

