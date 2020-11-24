import logging
import tempfile

from packages.util.command import run_command

logger = logging.getLogger(__name__)


def create_ns(ns: str):
    output, rc = run_command(command=["kubectl", "create", "ns", ns], merge_stderr=True)
    if rc != 0:
        logger.error(f"create ns failed(exit with code {rc}), err: {output}")
        raise RuntimeError("kubectl error")


def delete_ns(ns: str):
    output, rc = run_command(command=["kubectl", "delete", "ns", ns])
    if rc != 0:
        logger.error(f"delete ns failed(exit with code {rc}), err: {output}")
        raise RuntimeError("kubectl error")


def apply(yaml_str: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    with open(tmp_file.name, 'w') as f:
        f.write(yaml_str)

    output, rc = run_command(command=["kubectl", "apply", "-f", tmp_file.name], merge_stderr=True)
    if rc != 0:
        logger.error(f"apply yaml file failed(exit with code {rc}), err: {output}")
        raise RuntimeError("kubectl error")
    return tmp_file.name


def delete(yaml_file: str):
    output, rc = run_command(command=["kubectl", "delete", "-f", yaml_file])
    if rc != 0:
        logger.error(f"delete yaml file failed(exit with code {rc}), err: {output}")
        raise RuntimeError("kubectl error")
