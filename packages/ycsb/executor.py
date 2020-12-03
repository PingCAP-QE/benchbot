import json
import logging
import random
import string

from packages.util import kubectl, naglfar
from packages.util.version import cluster_version

logger = logging.getLogger(__name__)


class YCSBBenchmark:
    def __init__(self, args):
        self.args = dict()
        for key, value in vars(args).items():
            self.args[key] = value
        # generate ns
        letters = string.ascii_lowercase
        digits = string.digits
        self.ns = "naglfar-benchbot-ycsb-{letters}-{digits}".format(
            letters=''.join(random.choice(letters) for _ in range(5)),
            digits=''.join(random.choice(digits) for _ in range(9)))

    def get_version(self):
        return self.args["version"]

    def get_tidb_version(self):
        return self.args["tidb"]

    def get_tikv_version(self):
        return self.args["tikv"]

    def get_pd_version(self):
        return self.args["pd"]

    def get_baseline_version(self):
        return self.args["baseline_version"]

    def get_baseline_tidb_version(self):
        return self.args["baseline_tidb"]

    def get_baseline_tikv_version(self):
        return self.args["baseline_tikv"]

    def get_baseline_pd_version(self):
        return self.args["baseline_pd"]

    def get_name(self):
        return self.args["name"]

    def run(self):
        try:
            kubectl.create_ns(self.ns)
            _ = kubectl.apply(self.gen_test_resource_request())
            naglfar.wait_request_ready(self.ns, YCSBBenchmark.request_name())
            self.run_with_baseline()
        finally:
            kubectl.delete_ns(self.ns)

    def run_with_baseline(self):
        pr_results = self.run_naglfar(version=self.get_version(),
                                      tidb_url=self.get_tidb_version(),
                                      tikv_url=self.get_tikv_version(),
                                      pd_url=self.get_pd_version())

        base_results = self.run_naglfar(version=self.get_baseline_version(),
                                        tidb_url=self.get_baseline_tidb_version(),
                                        tikv_url=self.get_baseline_tikv_version(),
                                        pd_url=self.get_baseline_pd_version())

        YCSBBenchmark.generate_report(base_results, pr_results)

    def run_naglfar(self,
                    version: str,
                    tidb_url: str = None,
                    pd_url: str = None,
                    tikv_url: str = None):
        tct_file = kubectl.apply(self.gen_test_cluster_topology(version=version,
                                                                tidb_download_url=tidb_url,
                                                                tikv_download_url=tikv_url,
                                                                pd_download_url=pd_url))
        naglfar.wait_tct_ready(self.ns, YCSBBenchmark.tct_name())
        host_ip, port = naglfar.get_mysql_endpoint(ns=self.ns, tidb_node=YCSBBenchmark.tidb_node())
        version = cluster_version(tidb_host=host_ip, tidb_port=port)

        tw_file = kubectl.apply(self.gen_test_workload(version=self.get_version()))
        naglfar.wait_tw_status(self.ns, YCSBBenchmark.tw_name(), lambda status: status != "'pending'")

        std_log = naglfar.tail_tw_logs(self.ns, YCSBBenchmark.tw_name())
        # result = json.loads(std_log.strip().split('\n')[-1])
        result = YCSBBenchmark.get_workload_result(std_log.strip())

        naglfar.wait_tw_status(self.ns, YCSBBenchmark.tw_name(), lambda status: status == "'finish'")
        kubectl.delete(tw_file)
        kubectl.delete(tct_file)
        return {
            "cluster_info": version,
            "bench_result": result,
        }

    @staticmethod
    def request_name():
        return "tidb-cluster"

    @staticmethod
    def tct_name():
        return "tidb-cluster"

    @staticmethod
    def tw_name():
        return "ycsb-100m"

    @staticmethod
    def tidb_node():
        return "n1"

    def gen_test_resource_request(self) -> str:
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestResourceRequest
metadata:
  name: {YCSBBenchmark.request_name()}
  namespace: {self.ns}
spec:
  items:
    - name: {YCSBBenchmark.tidb_node()}
      spec:
        memory: 130GB
        cores: 30
        disks:
          disk1:
            kind: nvme
            mountPath: /disk1
        testMachineResource: 172.16.5.69
    - name: workload
      spec:
        memory: 20GB
        cores: 8
        testMachineResource: 172.16.5.69
"""

    def gen_test_cluster_topology(self, version: str,
                                  tikv_download_url=None,
                                  tidb_download_url=None,
                                  pd_download_url=None) -> str:
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestClusterTopology
metadata:
  name: {YCSBBenchmark.tct_name()}
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
      - host: n1
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

    def gen_test_workload(self, version: str) -> str:
        # path = "ycsb-100m"
        # if version.startswith("v4.0."):
        #     path = "ycsb-100m-release4.0"
        #
        return f"""
apiVersion: naglfar.pingcap.com/v1
kind: TestWorkload
metadata:
  name: {YCSBBenchmark.tw_name()}
  namespace: {self.ns}
spec:
  clusterTopologies:
    - name: {YCSBBenchmark.tct_name()}
      aliasName: cluster
  workloads:
    - name: {YCSBBenchmark.tw_name()}
      dockerContainer:
        resourceRequest:
          name: {YCSBBenchmark.request_name()}
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
            pd=`echo $cluster_pd0 | awk -F ":" '{{print $1}}'`

            echo "recordcount=100000000" >> global.conf
            echo "operationcount=1000000" >> global.conf
            echo "workload=core" >> global.conf
            echo "fieldcount=10" >> global.conf
            echo "fieldlength=100" >> global.conf
            echo "threadcount=500" >> global.conf

            br restore db --db=test --pd $pd:2379 --storage s3://mybucket/ycsb-100m-release4.0 \\
                --s3.endpoint http://172.16.4.4:30812 --send-credentials-to-tikv=true
            
            go-ycsb run mysql \\
                -P /ycsb/workloads/{self.get_name()} \\
                -P global.conf \\
                -p mysql.host=$tidb \\
                -p mysql.port=4000
"""

    @staticmethod
    def get_workload_result(result_str):
        results = result_str.split("\n")
        ret = {}
        skip = True
        for result in results:
            if not result.strip():
                continue
            if not skip:
                if "-" not in result:
                    continue
                res = YCSBBenchmark.parse_line(result)
                ret[res["key"].lower()] = res["value"]
            if "Run finished" in result:
                skip = False
        return ret

    @staticmethod
    def parse_line(line):
        # line: INSERT - Takes(s): 5601.5, Count: 100000000, OPS: 17852.4, Avg(us): 27503, Min(us): 1512,
        # Max(us): 527270, 99th(us): 48000, 99.9th(us): 62000, 99.99th(us): 92000
        key = line.split("-")[0].strip()
        values_str = line.split("-")[1].split(",")
        values = {}
        for valueStr in values_str:
            k = valueStr.split(":")[0].strip()
            v = valueStr.split(":")[1].strip()
            values[k] = v
        """
        {
            "INSERT": {"Count": "100000000", "OPS": "17852.4", "Avg(us)": "27503"}
        }
        """
        return {"key": key, "value": values}

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

> Run YCSB Performance Test on Naglfar

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
        current = current_bench_result["bench_result"]
        previous = baseline_bench_result["bench_result"]

        print("""baseline benchmark result:""")
        for key, value in previous.items():
            print(f"""\t{key}: {json.dumps(value)}""")

        print("""current benchmark result:""")
        for key, value in current.items():
            print(f"""\t{key}: {json.dumps(value)}""")

        print("```")
