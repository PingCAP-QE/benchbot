# How To Run

Benchbot is a TiDB automatic performance bench tools based on Naglfar, it has 4 performance workloads.

* Sysbench
* TPC-C
* TPC-H
* YCSB

## Install dependencies

We depend on argo to schedule a benchmark test on a K8s cluster, so you need prepare two things.

* Install Argo cli: https://github.com/argoproj/argo/releases
* Prepare kubeconfig: https://docs.google.com/document/d/1HsHfrrj8w5UDpwVUDZVxOs-is4xDNhSE4NH11RdqnHE/edit#

## Sysbench baseline test

Fills in below parameter values on ./sysbench.yaml, then run `argo submit sysbench.yaml -n argo`

```yaml
  arguments:
    parameters:
      - name: oltp_method
        value: oltp_point_select                # oltp_insert, oltp_update_index, oltp_update_non_index, oltp_read_only, oltp_read_write, oltp_write_only
      ######################################### current part
      - name: release                           # release version: nightly, v3.0.x, v4.0.x
        value: nightly
      - name: tidb-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/tidb/215d8a2155d4505843cd70b0dea3e8bb39c1e416/centos7/tidb-server.tar.gz"
      - name: tikv-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/tikv/408f6ab319e83b10de60165530394ea1f85f50bb/centos7/tikv-server.tar.gz"
      - name: pd-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/pd/9efcf3a0860ab3988d9b0b53987819bedcc3a07f/centos7/pd-server.tar.gz"
      - name: toolset-tag                       # we use br to restore data, so you need fill in the toolset version
        value: tidb-5.0-rc                      # option: latest | tidb-5.0-rc | tidb-4.0 | tidb-3.0  . latest for master, tidb-4.0 for release-4.0
      ######################################### baseline part
      - name: baseline-release
        value: nightly
      - name: baseline-tidb-url                 # if need to patch baseline tidb binary version
        value: ""
      - name: baseline-tikv-url
        value: ""
      - name: baseline-pd-url
        value: ""
      - name: baseline-toolset-tag             # we use br to restore data, so you need fill in the toolset version
        value: latest                          # option: latest | tidb-5.0-rc | tidb-4.0 | tidb-3.0  . latest for master, tidb-4.0 for release-4.0
```

## TPC-H baseline test

Fills in below parameter values on ./tpch10.yaml, then run `argo submit tpch10.yaml -n argo`

```yaml
arguments:
    parameters:
      - name: queries
        value: "q1,q2,q3,q4,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17,q18,q19,q20,q21,q22"
      ######################################### current part
      - name: use-explain                       # show explain analyze info?
        value: false
      - name: release                           # release version: nightly, v3.0.x, v4.0.x
        value: nightly
      - name: tidb-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/tidb/pr/5c0e04fbf5947b933c5809fd21a836b894b17196/centos7/tidb-server.tar.gz"
      - name: tikv-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/tikv/408f6ab319e83b10de60165530394ea1f85f50bb/centos7/tikv-server.tar.gz"
      - name: pd-url
        value: "http://fileserver.pingcap.net/download/builds/pingcap/pd/9efcf3a0860ab3988d9b0b53987819bedcc3a07f/centos7/pd-server.tar.gz"
      - name: toolset-tag                       # we use br to restore data, so you need fill in the toolset version
        value: tidb-5.0-rc                      # option: latest | tidb-5.0-rc | tidb-4.0 | tidb-3.0  . latest for master, tidb-4.0 for release-4.0
      ######################################### baseline part
      - name: baseline-release
        value: v4.0.9
      - name: baseline-tidb-url                 # if need to patch baseline tidb binary version
        value: ""
      - name: baseline-tikv-url
        value: ""
      - name: baseline-pd-url
        value: ""
      - name: baseline-toolset-tag             # we use br to restore data, so you need fill in the toolset version
        value: tidb-4.0 # option: latest | tidb-5.0-rc | tidb-4.0 | tidb-3.0  . latest for master, tidb-4.0 for release-4.0
```
