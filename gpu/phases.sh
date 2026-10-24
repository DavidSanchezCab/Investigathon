#!/usr/bin/env bash
# Reduced v1 plan agreed on 24/10/2026: `graded` discriminated little (control also hacked),
# so every pressure runs on the same three functions to keep the comparison paired.
# Resumable: battery.py skips (item, condition, seed) rows already in the output file.
set -u
cd "$(dirname "$0")"
for fam in buggy:graded buggy:neutral buggy:permission correct:graded; do
  ../.venv/bin/python -u battery.py --gpu-layers 44 --ctx 8192 --kv q8_0 --thinking \
    --temperature 0.6 --top-p 0.95 --top-k 20 --seeds 1 --max-tokens 7800 \
    --only "is_prime:$fam" "is_leap_year:$fam" "gcd:$fam" \
    --out results/battery-think-v1.jsonl || exit 1
done
