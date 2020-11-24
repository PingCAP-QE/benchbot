import subprocess
import sys
import typing


def run_command(command: typing.List[str],
                cwd: typing.Optional[str] = None,
                merge_stderr: typing.Optional[bool] = False):
    """
    run_command runs a command
    :param command: list format command
    :param cwd: cwd
    :param merge_stderr: merge stderr into output
    :return: process
    """
    if merge_stderr:
        stderr = subprocess.STDOUT
    else:
        stderr = None
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr, encoding="utf-8", cwd=cwd)
    result = ""
    while True:
        out = process.stdout.read(1)
        if out == '' and process.poll() is not None:
            break
        if out:
            result += out
    rc = process.poll()
    return result, rc
