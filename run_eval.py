#!/usr/bin/env python3
"""Run the five saved criteria and write the raw measurements."""

import argparse

from measure import run_measurement, save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=["before", "after"])
    args = parser.parse_args()
    save(run_measurement(), args.label)


if __name__ == "__main__":
    main()
