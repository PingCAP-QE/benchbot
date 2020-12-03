## Install the project

```sh
pip3 install -r requirements.txt
pip3 install -e .
```

## How to run

### Update image

```sh
docker pull hub.pingcap.net/mahjonp/benchbot:latest
```

### Get the help info

```sh
docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest $workload --help
```

### Run TPC-C

```sh
# run the tpcc workload with a specified tikv git_hash: 164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d
docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest tpcc \
        -tikv http://fileserver.pingcap.net/download/builds/pingcap/tikv/164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d/centos7/tikv-server.tar.gz
```

### Run Sysbench OLTP

```sh
# run the sysbench oltp_update_index workload with a a specified tikv git_hash
docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest sysbench \
        -name oltp_update_index \
        -baseline-version v4.0.8 \
        -version v4.0.8 -tikv http://fileserver.pingcap.net/download/builds/pingcap/tikv/164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d/centos7/tikv-server.tar.gz
```

### Run YCSB

```sh
docker run -v ~/.kube:/root/.kube -it hub.pingcap.net/mahjonp/benchbot:latest ycsb \
        -name workloada \
        -baseline-version v4.0.8 \
        -version v4.0.8 -tikv http://fileserver.pingcap.net/download/builds/pingcap/tikv/164eb3d2dc94064f80b3ad3f6ae21cb071aaf36d/centos7/tikv-server.tar.gz
```
