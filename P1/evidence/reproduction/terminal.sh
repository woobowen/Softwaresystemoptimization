#!/bin/bash
set -e
trap 'rc=$?; printf "%s\n" "$rc" > /tmp/p1-goal1-reproduction-ltmlbuch/P1/.cache/independent-final/done' EXIT
cd /tmp/p1-goal1-reproduction-ltmlbuch
clear
printf 'P1 Matrix Multiplication Autotuner - fresh clone\n'
printf 'Fresh run; separate from stored benchmarks\n'
pwd
python3 -B P1/.cache/independent-final/run_step.py build python3 -B P1/src/autotuner.py build --compile-timeout 60 --cache-dir P1/.cache/independent-final/build --output P1/.cache/independent-final/build.jsonl
python3 -B P1/.cache/independent-final/run_step.py run taskset -c 0 python3 -B P1/src/autotuner.py run --s 128 --opt O3 --seed 0 --repeats 1 --timeout 1200 --compile-timeout 60 --min-trials 5 --patience 3 --min-relative-improvement 0.06 --protocol P1/evidence/protocol_v1.json --cache-dir P1/.cache/independent-final/build --output P1/.cache/independent-final/run.jsonl
