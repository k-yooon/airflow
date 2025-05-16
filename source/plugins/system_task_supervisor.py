from datetime import datetime, timezone

from airflow import settings
from airflow.decorators import dag
from airflow.models import DagRun, TaskInstance
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.state import State


default_args = {
    'owner': 'kyoon lee',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 3, tzinfo=const.LOCAL_TIMEZONE)
}


@dag(
    default_args=default_args,
    description='system task supervisor',
    schedule='53 * * * *',
    catchup=False,
    tags=['airflow', 'system']
)
def system_task_supervisor():
    task_state_list = ['running', 'queued']

    def monitor_task_state(state: str, **context):
        config = Variable.get("supervisor_config", default_var={}, deserialize_json=True)
        allow_time = {
            'running': config['allow_running_time'],
            'queued': config['allow_queued_time']
        }.get(state)

        airflow_state = {
            'running': State.RUNNING,
            'queued': State.QUEUED
        }.get(state)

        session = settings.Session()
        running_dags = session.query(DagRun).filter(
            DagRun.dag_id != context['dag_run'].dag_id,
            DagRun.state == 'running'
        ).all()

        if running_dags:
            for dag in running_dags:
                tasks = session.query(TaskInstance).filter(
                    TaskInstance.dag_id == dag.dag_id,
                    TaskInstance.execution_date == dag.execution_date,
                    TaskInstance.state == state
                ).all()

                if tasks:
                    failed_list = []
                    for ti in tasks:
                        if ti.state == airflow_state:
                            duration = (datetime.now(timezone.utc) - dag.start_date).seconds
                            if duration > allow_time:
                                print(
                                    f"Task '{ti.task_id}' in DAG '{ti.dag_id}' is {state} for {duration} seconds. "
                                    "set state to FAILED")
                                ti.set_state(State.FAILED)
                                session.commit()
                                failed_list.append(ti.task_id)
                            else:
                                print(
                                    f"Task '{ti.task_id}' in DAG '{ti.dag_id}' is {state} for {duration} seconds. "
                                    "not yet to FAILED")

                    if failed_list:
                        raise Exception(f'Some tasks are {state} for too long. check the logs')
        else:
            print('No running dags')

        session.close()

    for state in task_state_list:
        monitor_task = PythonOperator(
            task_id=f'monitor_{state}_tasks',
            python_callable=monitor_task_state,
            op_kwargs={'state': state}
        )

        monitor_task


system_task_supervisor()
