#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import argparse
import logging

from packages.ycsb.executor import YCSBBenchmark


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    arguments = argparse.ArgumentParser()
    arguments.add_argument("-version", type=str, required=True, help="set version, eg: nightly,v4.0.8")
    arguments.add_argument("-tidb", type=str, help="the tidb download URL")
    arguments.add_argument("-tikv", type=str, help="the tikv download URL")
    arguments.add_argument("-pd", type=str, help="the pd download URL")
    arguments.add_argument("-toolset", type=str, required=True,
                           help="set bench-toolset version, eg: latest,tidb-3.0,tidb-4.0,tidb-5.0-rc")

    arguments.add_argument("-baseline-version", required=False, type=str,
                           help="set baseline version, eg: nightly,v4.0.8")
    arguments.add_argument("-baseline-tidb", type=str, help="set the baseline tidb download URL")
    arguments.add_argument("-baseline-tikv", type=str, help="the the baseline tikv download URL")
    arguments.add_argument("-baseline-pd", type=str, help="the the baseline pd download URL")
    arguments.add_argument("-baseline-toolset", type=str, required=True,
                           help="set baseline bench-toolset version, eg: latest,tidb-3.0,tidb-4.0,tidb-5.0-rc")

    arguments.add_argument("-name", type=str, required=True, default="workloada",
                           help="workload name, eg. workloada, workloadb, workloadc etc.")
    args = arguments.parse_args()

    YCSBBenchmark(args).run()


if __name__ == "__main__":
    main()
