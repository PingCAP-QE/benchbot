#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import argparse
import logging

from packages.ycsb.executor import YCSBBenchmark


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    arguments = argparse.ArgumentParser()
    arguments.add_argument("-branch", type=str, default="master", help="The branch name")
    arguments.add_argument("-repeat_time", type=int, default=3, help="The repeat time")
    arguments.add_argument("-workload", type=str, help="The workload")
    arguments.add_argument("-mode", type=str, default="mysql", help="The mode, eg: raw/txn")
    args = arguments.parse_args()

    YCSBBenchmark(args).run()


if __name__ == "__main__":
    main()
