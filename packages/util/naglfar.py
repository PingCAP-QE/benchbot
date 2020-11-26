import logging
import re
import time

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


def wait_tw_status(ns: str, name: str, predicate):
    for _ in range(60):
        output, rc = run_command(command=["kubectl", "get", "tw", name, "-n", ns, "-o", "jsonpath='{.status.state}'"],
                                 merge_stderr=True)
        if rc != 0:
            logger.error(f"get the status of tw {ns}/{name} failed, err: {output}")
            time.sleep(120)
        elif predicate(output):
            logger.info(f"the tw {ns}/{name} is {output}")
            return
        else:
            logger.info(f"the state of tw {ns}/{name} is {output}, waiting...")
            time.sleep(120)


def tail_tw_logs(ns: str, name: str) -> str:
    content, rc = run_command(command=["naglfar", "logs", "-n", ns, "--follow", name],
                              merge_stderr=False,
                              print_log_to_stderr=True)
    if rc != 0:
        raise RuntimeError("naglfar logs error")

    return content
