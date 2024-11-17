from datetime import timedelta, datetime, timezone

import common.constant.Global
from airflow.models import BaseOperator
from airflow.models import DagRun
from common.tool.SlackUtil import SlackAlert

from airflow import settings

alert = SlackAlert(.SLACK_CHANNEL_PROD)


class CheckRunTimeOperator(BaseOperator):

    def __init__(
        self,
        num_dags: int = 3,
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.num_dags = num_dags

    def execute(self, context):
        dag_id = context['dag_run'].dag_id
        num_dags = self.num_dags
        session = settings.Session()
        last_runs = session.query(DagRun).filter(
            DagRun.dag_id == dag_id,
            DagRun.state == 'success'
        ).order_by(DagRun.execution_date.desc()).limit(num_dags).all()

        now_run = session.query(DagRun).filter(
            DagRun.dag_id == dag_id,
            DagRun.state == 'running'
        ).order_by(DagRun.execution_date.desc()).limit(1).all()

        if len(last_runs) < num_dags:
            return

        start_date = datetime.fromisoformat(str(now_run[0].start_date))
        duration = (datetime.now(timezone.utc) - start_date).seconds

        total_run_time = sum([run.end_date - run.start_date for run in last_runs], timedelta(0))
        avg_run_time = (total_run_time / num_dags).seconds

        if duration > avg_run_time * 2:
            context['avg_run_time'] = f'{avg_run_time // 60}m {avg_run_time % 60}s'
            context['duration'] = f'{duration // 60}m {duration % 60}s'
            alert.slack_warning_alert(context)

