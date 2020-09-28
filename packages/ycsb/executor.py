import json
import logging
import os
import subprocess
import sys

from packages.util import stat
from packages.util.apiserver import upload_report, retrieve_reports, clean_cluster_data
from packages.util.version import cluster_version
from packages.ycsb.util import get_workload_result

tidb_host = str.split(os.getenv("TIDB_ADDR"), ":")[0]
tidb_port = str.split(os.getenv("TIDB_ADDR"), ":")[1]

logger = logging.getLogger(__name__)


class YCSBBenchmark:
    def __init__(self, args):
        self.args = dict()
        for key, value in vars(args).items():
            if value is not None:
                self.args[key] = value

    def get_workload(self):
        return self.args["workload"]

    def get_repeat_time(self):
        return int(self.args["repeat_time"])

    def get_mode(self):
        return self.args["mode"]

    def run(self):
        workload = self.get_workload()
        results = []
        for i in range(self.get_repeat_time()):
            results.append(self.do_bench_mysql(workload=workload))
            clean_cluster_data()

        bench_result = dict()
        for op, _ in results[0].items():
            bench_result[op] = dict()
            for item in ["OPS", "Avg(us)", "99th(us)"]:
                tmp_list = []
                tmp_list.extend(float(row[op][item]) for row in results)
                tmp_dict = stat.compute_stats(tmp_list)
                bench_result[op][item] = tmp_dict

        bench_report = {
            "cluster_info": cluster_version(tidb_host=tidb_host, tidb_port=tidb_port),
            "bench_result": bench_result,
        }
        reports = retrieve_reports()
        if len(reports) == 0:
            upload_report(data=json.dumps(bench_report), plaintext=None)
        else:
            plain_report = self.generate_report(reports, bench_report)
            upload_report(data=json.dumps(bench_report), plaintext=plain_report)

    @staticmethod
    def do_bench_mysql(workload):
        cwd = f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/ycsb"
        logger.info(f"cwd={cwd}")

        cmd = ["sh", "-c",
               f"""
                set -ex
               /bin/go-ycsb load mysql -P global.conf -p mysql.host={tidb_host} -p mysql.port={tidb_port}
                """]
        res = subprocess.run(cmd, cwd=cwd)

        if res.returncode != 0:
            logger.error(f"execute go-ycsb run mysql failed, exit with code {res.returncode}")
            raise RuntimeError("ycsb load data error")

        cmd = ["sh", "-c",
               f"""set -ex
               /bin/go-ycsb run mysql \\
               -P workloads/{workload} \\
               -P global.conf \\
               -p mysql.host={tidb_host} \\
               -p mysql.port={tidb_port}
               """]
        res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE)

        if res.returncode != 0:
            logger.error(f"execute go-ycsb run mysql failed, exit with code {res.returncode}")
            raise RuntimeError("do_bench_mysql error")
        return get_workload_result(res.stdout.decode('utf-8'))

    @staticmethod
    def generate_report(baseline_bench_results, current_bench_result) -> str:
        baseline_bench_result = json.loads(baseline_bench_results[len(baseline_bench_results) - 1]["data"])
        print(json.dumps({
            "baseline": baseline_bench_result,
            "current": current_bench_result,
        }), file=sys.stderr)

        pre_tidb_commit = baseline_bench_result.get("cluster_info", {}).get("tidb", {}).get("git_hash", "")
        pre_tikv_commit = baseline_bench_result.get("cluster_info", {}).get("tikv", {}).get("git_hash", "")
        pre_pd_commit = baseline_bench_result.get("cluster_info", {}).get("pd", {}).get("git_hash", "")

        cur_tidb_commit = current_bench_result.get("cluster_info", {}).get("tidb", {}).get("git_hash", "")
        cur_tikv_commit = current_bench_result.get("cluster_info", {}).get("tikv", {}).get("git_hash", "")
        cur_pd_commit = current_bench_result.get("cluster_info", {}).get("pd", {}).get("git_hash", "")

        plain_report = """
## Benchmark Report

> Run GO-YCSB Performance Test

```diff
@@                               Benchmark Diff                               @@
==================================="""
        if cur_tidb_commit != pre_tidb_commit:
            plain_report += f"""
--- tidb: {pre_tidb_commit}
+++ tidb: {cur_tidb_commit}"""
        else:
            plain_report += f"""
tidb: {cur_tidb_commit}"""

        if cur_pd_commit != pre_pd_commit:
            plain_report += f"""
--- pd: {pre_pd_commit}
+++ pd: {cur_pd_commit}"""
        else:
            plain_report += f"""
pd: {cur_pd_commit}"""

        if cur_tikv_commit != pre_tikv_commit:
            plain_report += f"""
--- tikv: {pre_tikv_commit}
+++ tikv: {cur_tikv_commit}"""
        else:
            plain_report += f"""
tikv: {cur_tikv_commit}"""

        plain_report += """\n===================================\n"""

        for key, value in current_bench_result["bench_result"].items():
            cur_ops = value["OPS"]
        cur_avg_us = value["Avg(us)"]
        cur_99th_us = value["99th(us)"]

        baseline_ops = baseline_bench_result["bench_result"][key]["OPS"]["value"]
        baseline_avg_ms = baseline_bench_result["bench_result"][key]["Avg(us)"]["value"] / 1000
        baseline_99th_ms = baseline_bench_result["bench_result"][key]["99th(us)"]["value"] / 1000
        ops_delta = stat.delta(cur_ops["value"], baseline_ops)

        plain_report += """%s:
    * OPS: %.2f ± %.2f%% (std=%.2f) delta: %.2f%%
    * Avg: %.2f ± %.2f%% delta: %.2f%%
    * p99: %.2f ± %.2f%% delta: %.2f%%
""" % (
            key,
            cur_ops["value"], cur_ops["deviation"] * 100, cur_ops["std"], ops_delta,
            cur_avg_us["value"] / 1000, cur_avg_us["deviation"] * 100,
            stat.delta(cur_avg_us["value"] / 1000, baseline_avg_ms),
            cur_99th_us["value"] / 1000, cur_99th_us["deviation"] * 100,
            stat.delta(cur_99th_us["value"] / 1000, baseline_99th_ms)
        )
        plain_report += "```"
        return plain_report
