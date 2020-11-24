import json
import logging
import re
import time
import typing

from packages.util.command import run_command

logger = logging.getLogger(__name__)


def wait_request_ready(ns: str, name: str):
    for _ in range(10):
        output, rc = run_command(command=["kubectl", "get", "trr", name, "-n", ns, "-o", "jsonpath='{.status.state}'"],
                                 merge_stderr=True)
        if rc != 0:
            logger.error(f"get the status of request {ns}/{name} failed, err: {output}")
            time.sleep(60)
        elif output == "'ready'":
            logger.info(f"the request {ns}/{name} is ready")
            return
        else:
            logger.info(f"the state of request {ns}/{name} is {output}, waiting...")
            time.sleep(60)
    raise RuntimeError("wait request ready timeout")


def wait_tct_ready(ns: str, name: str):
    for _ in range(10):
        output, rc = run_command(command=["kubectl", "get", "tct", name, "-n", ns, "-o", "jsonpath='{.status.state}'"],
                                 merge_stderr=True)
        if rc != 0:
            logger.error(f"get the status of tct {ns}/{name} failed, err: {output}")
            time.sleep(60)
        elif output == "'ready'":
            logger.info(f"the tct {ns}/{name} is ready")
            return
        else:
            logger.info(f"the state of tct {ns}/{name} is {output}, waiting...")
            time.sleep(60)

    raise RuntimeError("wait request ready timeout")


def get_mysql_endpoint(ns: str, tidb_node: str) -> (str, str):
    output, rc = run_command(
        command=["kubectl", "get", "tr", tidb_node, "-n", ns, "-o", "jsonpath='{.status.hostIP}'"],
        merge_stderr=True)
    if rc != 0:
        logger.error(f"get the status of resource {ns}/{tidb_node} failed, err: {output}")
        raise RuntimeError("kubectl err")
    host_ip = output[1:-1]

    output, rc = run_command(
        command=["kubectl", "get", "tr", tidb_node, "-n", ns, "-o", "jsonpath='{.status.portBindings}'"],
        merge_stderr=True)
    if rc != 0:
        logger.error(f"get the status of resource {ns}/{tidb_node} failed, err: {output}")
        raise RuntimeError("kubectl err")
    port = re.search(r'4000/tcp:(\d+)', output).group(1)
    return host_ip, port


def wait_tw_finish(ns: str, name: str):
    for _ in range(60):
        output, rc = run_command(command=["kubectl", "get", "tw", name, "-n", ns, "-o", "jsonpath='{.status.state}'"],
                                 merge_stderr=True)
        if rc != 0:
            logger.error(f"get the status of tw {ns}/{name} failed, err: {output}")
            time.sleep(120)
        elif output == "'finish'":
            logger.info(f"the tw {ns}/{name} is finish")
            return
        else:
            logger.info(f"the state of tw {ns}/{name} is {output}, waiting...")
            time.sleep(120)


def get_tw_result(ns: str, name: str, item_name: str) -> typing.Any:
    output, rc = run_command(
        command=["kubectl", "get", "tw", name, "-n", ns, "-o", f"jsonpath='{{.status.results.{item_name}.plainText}}'"],
        merge_stderr=True)
    if rc != 0:
        logger.error(f"get the result of workload {ns}/{name}/{item_name} failed, err: {output}")
        raise RuntimeError("kubectl err")
    if output == "":
        logger.error("emm, get nothing :(")
    logger.info(f"tw_result: {output}")
    return json.loads(output[1:-1])
