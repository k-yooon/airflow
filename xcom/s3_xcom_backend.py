import os
import uuid
import pandas as pd
import json

from typing import Any
from airflow.models.xcom import BaseXCom
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


class S3XComBackend(BaseXCom):
    PREFIX = "xcom_s3"
    BUCKET_NAME = os.environ.get("S3_XCOM_BUCKET_NAME")
    AWS_CONN_ID = os.environ.get("AWS_CONN_ID")

    @staticmethod
    def _assert_s3_backend():
        if S3XComBackend.BUCKET_NAME is None:
            raise ValueError("Unknown bucket for S3 backend.")

    @staticmethod
    def serialize_value(
        value: Any,
        key: str | None = None,
        task_id: str | None = None,
        dag_id: str | None = None,
        run_id: str | None = None,
        map_index: str | None = None,
        **kwargs
    ):
        if isinstance(value, pd.DataFrame):
            S3XComBackend._assert_s3_backend()
            hook = S3Hook(aws_conn_id=S3XComBackend.AWS_CONN_ID)
            filename = f"data_{str(uuid.uuid4())}.csv"
            key = f"airflow/xcom/{dag_id}/{run_id}/{task_id}/{filename}"
            value.to_csv(filename, index=False)
            
            hook.load_file(
                filename=filename,
                key=key,
                bucket_name=S3XComBackend.BUCKET_NAME,
                replace=True
            )
            
            value = f"{S3XComBackend.PREFIX}://{key}"

        return BaseXCom.serialize_value(value)

    @staticmethod
    def deserialize_value(result) -> Any:
        result = BaseXCom.deserialize_value(result)

        if isinstance(result, str) and result.startswith(S3XComBackend.PREFIX):
            S3XComBackend._assert_s3_backend()
            hook = S3Hook(aws_conn_id=S3XComBackend.AWS_CONN_ID)
            key = result.replace(f"{S3XComBackend.PREFIX}://", "")
            filename = hook.download_file(
                key=key,
                bucket_name=S3XComBackend.BUCKET_NAME,
                local_path="/tmp"
            )
            result = pd.read_csv(filename)

        return result