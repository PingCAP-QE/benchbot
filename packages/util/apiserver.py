import json
import logging
import os
import time
from typing import Optional

import requests

cr_id = os.getenv("CLUSTER_ID")
api_server = os.getenv("API_SERVER")

logger = logging.getLogger(__name__)


def upload_report(data: str, plaintext: Optional[str]):
    """
    upload report to the api_server
    :param data: str, the serialized data string
    :param plaintext: Optional[str], the plain text format report
    :return:
    """
    d = {
        "data": data
    }
    if plaintext is not None:
        d["plaintext"] = plaintext
    logger.info("uploading %s...", json.dumps(d))
    r = requests.post(url=f"{api_server}/api/cluster/workload/{cr_id}/result", json=d)
    if r.status_code != 200:
        raise RuntimeError(r.content)


def retrieve_reports():
    """
    retrieve reports from the api_server according to $cr_id
    :return: a json of format: [{"data": str, plaintext: Optional[str]}, ...]
    """
    r = requests.get(url=f"{api_server}/api/cluster/workload/{cr_id}/result")
    if r.status_code != 200:
        raise RuntimeError(r.content)
    logger.info("retrieve report of %s: %s", cr_id, r.content)
    return r.json()


def clean_cluster_data():
    """
    request api_server to clean up cluster data
    :return:
    """
    r = requests.get(url=f"{api_server}/api/cluster/clean/{cr_id}")
    if not r.ok:
        raise RuntimeError(r.content)

    wait = 0
    while True:
        r = requests.get(url=f"{api_server}/api/cluster/{cr_id}")
        if not r.ok:
            raise RuntimeError(r.content)
        data = r.json()
        if data["status"] == "RUNNING":
            break
        wait += 1
        if wait == 6 * 10:
            raise RuntimeError("wait clean cluster data timeout")
        logger.info("wait cluster status to be RUNNING, current is: %s", data["status"])
        time.sleep(10)
