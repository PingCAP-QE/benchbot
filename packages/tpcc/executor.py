import json
import logging
import random
import string

from packages.util import kubectl, naglfar
from packages.util import stat
from packages.util.version import cluster_version

logger = logging.getLogger(__name__)


class TPCCBenchmark:
    def __init__(self, args):
        self.args = dict()
        for key, value in vars(args).items():
            self.args[key] = value
        # generate ns
        letters = string.ascii_lowercase
        digits = string.digits
        self.ns = "naglfar-benchbot-tpcc-{letters}-{digits}".format(
            letters=''.join(random.choice(letters) for _ in range(5)),
            digits=''.join(random.choice(digits) for _ in range(9)))

    def get_tidb_version(self):
        return self.args["tidb"]

    def get_tikv_version(self):
        return self.args["tikv"]

    def get_pd_version(self):
        return self.args["pd"]

    def get_baseline_tidb_version(self):
        return self.args["baseline_tidb"]

    def get_baseline_tikv_version(self):
        return self.args["baseline_tikv"]

    def get_baseline_pd_version(self):
        return self.args["baseline_pd"]

    def run(self):
        try:
            kubectl.create_ns(self.ns)
            _ = kubectl.apply(self.gen_test_resource_request())
            naglfar.wait_request_ready(self.ns, TPCCBenchmark.request_name())
            self.run_with_baseline()
        finally:
            kubectl.delete_ns(self.ns)

    def run_with_baseline(self):
        pr_results = self.run_naglfar(version="nightly",
                                      tidb_url=self.get_tidb_version(),
                                      tikv_url=self.get_tikv_version(),
                                      pd_url=self.get_pd_version())

        base_results = self.run_naglfar(version="nightly",
                                        tidb_url=self.get_baseline_tidb_version(),
                                        tikv_url=self.get_baseline_tikv_version(),
                                        pd_url=self.get_baseline_pd_version())

        TPCCBenchmark.generate_report(base_results, pr_results)

    def run_naglfar(self,
                    version: str,
                    tidb_url: str = None,
                    pd_url: str = None,
                    tikv_url: str = None):
        tct_file = kubectl.apply(self.gen_test_cluster_topology(version=version,
                                                                tidb_download_url=tidb_url,
                                                                tikv_download_url=tikv_url,
                                                                pd_download_url=pd_url))
        naglfar.wait_tct_ready(self.ns, TPCCBenchmark.tct_name())
        host_ip, port = naglfar.get_mysql_endpoint(ns=self.ns, tidb_node=TPCCBenchmark.tidb_node())
        version = cluster_version(tidb_host=host_ip, tidb_port=port)

        tw_file = kubectl.apply(self.gen_test_workload())
        naglfar.wait_tw_status(self.ns, TPCCBenchmark.tw_name(), lambda status: status != "'pending'")

        std_log = naglfar.tail_tw_logs(self.ns, TPCCBenchmark.tw_name())
        result = json.loads(std_log.strip().split('\n')[-1])

        naglfar.wait_tw_status(self.ns, TPCCBenchmark.tw_name(), lambda status: status == "'finish'")
        kubectl.delete(tw_file)
        kubectl.delete(tct_file)
        return {
            "cluster_info": version,
            "bench_result": TPCCBenchmark.process_bench_result(result)
        }

    @staticmethod
    def process_bench_result(data) -> float:
        for item in data:
            if item["type"] == "NEW_ORDER" and item["name"] == "tpm":
                return float(item["value"])
        raise RuntimeError("NEW_ORDER not found")

    @staticmethod
    def request_name():
        return "tidb-cluster"

    @staticmethod
    def tct_name():
        return "tidb-cluster"

    @staticmethod
    def tw_name():
        return "tpcc200"

    @staticmethod
    def tidb_node():
        return "n1"

    def gen_test_resource_request(self) -> str:
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestResourceRequest
metadata:
  name: {TPCCBenchmark.request_name()}
  namespace: {self.ns}
spec:
  items:
    - name: {TPCCBenchmark.tidb_node()}
      spec:
        memory: 10GB
        cores: 10
#        disks:
#          disk1:
#            kind: nvme
#            size: 500GB
#            mountPath: /disks1
    - name: n2
      spec:
        memory: 10GB
        cores: 10
        disks:
#          disk1:
#            kind: nvme
#            size: 1TB
#            mountPath: /disks1
    - name: workload
      spec:
        memory: 10GB
        cores: 10
"""

    def gen_test_cluster_topology(self, version: str,
                                  tikv_download_url=None,
                                  tidb_download_url=None,
                                  pd_download_url=None) -> str:
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestClusterTopology
metadata:
  name: {TPCCBenchmark.tct_name()}
  namespace: {self.ns}
spec:
  resourceRequest: tidb-cluster
  tidbCluster:
    serverConfigs:
      tidb: |-
      tikv: |-
      pd: |-
    version:
      version: {version}
      tikvDownloadURL: {tikv_download_url or '""'}
      tidbDownloadURL: {tidb_download_url or '""'}
      pdDownloadURL: {pd_download_url or '""'}
    control: n1
    tikv:
      - host: n2
        port: 20160
        statusPort: 20180
        deployDir: /disk1/deploy/tikv-20160
        dataDir: /disk1/data/tikv-20160
        logDir: /disk1/deploy/tikv-20160/log
    tidb:
      - host: n1
        deployDir: /disk1/deploy/tidb-4000
    pd:
      - host: n1
        deployDir: /disk1/deploy/pd-2379
        dataDir: /disk1/data/pd-2379
        logDir: /disk1/deploy/pd-2379/log
    monitor:
      - host: n1
        deployDir: /disk1/deploy/prometheus-8249
        dataDir: /disk1/deploy/prometheus-8249/data
    grafana:
      - host: n1
        deployDir: /disk1/deploy/grafana-3000
"""

    def gen_test_workload(self) -> str:
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestWorkload
metadata:
  name: {TPCCBenchmark.tw_name()}
  namespace: {self.ns}
spec:
  clusterTopologies:
    - name: {TPCCBenchmark.tct_name()}
      aliasName: cluster
  workloads:
    - name: {TPCCBenchmark.tw_name()}
      dockerContainer:
        resourceRequest:
          name: {TPCCBenchmark.request_name()}
          node: workload
        image: "hub.pingcap.net/mahjonp/bench-toolset"
        imagePullPolicy: Always
        command:
          - /bin/sh
          - -c
          - |
            set -ex
            export AWS_ACCESS_KEY_ID=YOURACCESSKEY AWS_SECRET_ACCESS_KEY=YOURSECRETKEY
            tidb=`echo $cluster_tidb0 | awk -F ":" '{{print $1}}'`
            bench-toolset bench tpcc \
             --host $tidb --port 4000 \
             --warehouses 200 \
             --time 30m \
             --threads 200 \
             --log "/var/log/test.log" \
             --br-args "db" \
             --br-args "--db=test" \
             --br-args "--pd=$cluster_pd0" \
             --br-args "--storage=s3://mybucket/tpcc-200" \
             --br-args "--s3.endpoint=http://172.16.4.4:30812" \
             --br-args "--send-credentials-to-tikv=true" \
             --json
"""

    @staticmethod
    def generate_report(baseline_bench_result, current_bench_result):
        # debug
        logger.info(json.dumps({
            "baseline": baseline_bench_result,
            "current": current_bench_result,
        }))
        pre_tidb_commit = baseline_bench_result.get("cluster_info", {}).get("tidb", {}).get("git_hash", "")
        pre_tikv_commit = baseline_bench_result.get("cluster_info", {}).get("tikv", {}).get("git_hash", "")
        pre_pd_commit = baseline_bench_result.get("cluster_info", {}).get("pd", {}).get("git_hash", "")

        cur_tidb_commit = current_bench_result.get("cluster_info", {}).get("tidb", {}).get("git_hash", "")
        cur_tikv_commit = current_bench_result.get("cluster_info", {}).get("tikv", {}).get("git_hash", "")
        cur_pd_commit = current_bench_result.get("cluster_info", {}).get("pd", {}).get("git_hash", "")

        print("""## Benchmark Report

> Run TPC-C Performance Test on Naglfar

```diff
@@                               Benchmark Diff                               @@
================================================================================""")
        if cur_tidb_commit != pre_tidb_commit:
            print(f"""--- tidb: {pre_tidb_commit}
+++ tidb: {cur_tidb_commit}""")
        else:
            print(f"tidb: {cur_tidb_commit}")

        if cur_tikv_commit != pre_tikv_commit:
            print(f"""--- tikv: {pre_tikv_commit}
+++ tikv: {cur_tikv_commit}""")
        else:
            print(f"tikv: {cur_tikv_commit}")

        if cur_pd_commit != pre_pd_commit:
            print(f"""--- pd: {pre_pd_commit}
+++ pd: {cur_pd_commit}""")
        else:
            print(f"pd: {cur_pd_commit}")
        print("""================================================================================""")

        # print bench result and the comparison with previous data
        current_tpmc = current_bench_result["bench_result"]
        previous_tpmc = baseline_bench_result["bench_result"]
        tpmc_delta = stat.delta(current_tpmc, previous_tpmc)

        print("""Measured tpmC (NewOrders): %.2f, delta: %.2f%%"""
              % (current_tpmc, tpmc_delta))

        print("```")
