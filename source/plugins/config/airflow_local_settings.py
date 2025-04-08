from airflow.www.utils import UIAlert

def get_dashboard_alerts():
    import os
    import json
    import logging
    pod_name = os.environ.get("HOSTNAME", "")
    if "webserver" not in pod_name:
        return []
    file_path = '/opt/airflow/etc/alert_config.json'
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            alert_data = json.load(f).get('ui_message', {})
    except Exception as e:
        logging.warning(f'[UI_ALERT] Failed to load alert config: {e}')
        alert_data = {}

    return [
        UIAlert(msg, category=level, roles=['Admin', 'User'])
        for level in ('info', 'warning', 'error')
        for msg in alert_data.get(level, [])
    ]
