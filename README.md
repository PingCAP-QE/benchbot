## Install the project

```sh
pip3 install -r requirements.txt
pip3 install -e .
```

## Run

```sh
# get help info
$ docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest tpcc --help
usage: tpcc [-h] [-tidb TIDB] [-tikv TIKV] [-pd PD] [-baseline-tidb BASELINE_TIDB] [-baseline-tikv BASELINE_TIKV]
            [-baseline-pd BASELINE_PD]

optional arguments:
  -h, --help            show this help message and exit
  -tidb TIDB            tidb
  -tikv TIKV            tikv
  -pd PD                pd
  -baseline-tidb BASELINE_TIDB
                        tidb
  -baseline-tikv BASELINE_TIKV
                        tikv
  -baseline-pd BASELINE_PD
                        pd

$ docker pull hub.pingcap.net/mahjonp/benchbot:latest

# run the tpcc workload with a specified tikv git_hash: 164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d
$ docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest tpcc \
        -tikv http://fileserver.pingcap.net/download/builds/pingcap/tikv/164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d/centos7/tikv-server.tar.gz

# run the sysbench oltp_update_index workload with a a specified tikv git_hash
$ docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest sysbench \
        -name oltp_update_index \
        -baseline-version v4.0.8 \
        -version v4.0.8 -tikv http://fileserver.pingcap.net/download/builds/pingcap/tikv/164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d/centos7/tikv-server.tar.gz
```
