#!/usr/bin/env bash
# Remaining five functions of the v1 thinking grid, same configuration as phases.sh.
# Lowest priority: queued after the seed sweep.
set -u
cd "$(dirname "$0")"
for fam in buggy:graded buggy:neutral buggy:permission correct:graded; do
  ../.venv/bin/python -u battery.py --gpu-layers 44 --ctx 8192 --kv q8_0 --thinking \
    --temperature 0.6 --top-p 0.95 --top-k 20 --seeds 1 --max-tokens 7800 \
    --only "factorial:$fam" "count_vowels:$fam" "digit_sum:$fam" "fibonacci:$fam" \
           "celsius_to_fahrenheit:$fam" \
    --out results/battery-think-v1.jsonl || exit 1
done
