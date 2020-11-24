#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import argparse
import logging

from packages.tpcc.executor import TPCCBenchmark


def main():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    arguments = argparse.ArgumentParser()
    arguments.add_argument("-tidb", type=str, help="tidb")
    arguments.add_argument("-tikv", type=str, help="tikv")
    arguments.add_argument("-pd", type=str, help="pd")

    arguments.add_argument("-baseline-tidb", type=str, help="tidb")
    arguments.add_argument("-baseline-tikv", type=str, help="tikv")
    arguments.add_argument("-baseline-pd", type=str, help="pd")
    args = arguments.parse_args()

    TPCCBenchmark(args).run()


if __name__ == "__main__":
    main()
