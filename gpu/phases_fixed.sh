#!/usr/bin/env bash
# Added 25/10/2026, same settings as phases.sh. First `fixed:graded` on the three v1
# functions (pairs with their `buggy` rows), then `buggy:permission` on the other five,
# the variant where hacker and the references separated most. Resumable like phases.sh.
set -u
cd "$(dirname "$0")"
run() {
  ../.venv/bin/python -u battery.py --gpu-layers 44 --ctx 8192 --kv q8_0 --thinking \
    --temperature 0.6 --top-p 0.95 --top-k 20 --seeds 1 --max-tokens 7800 \
    --only "$@" --out results/battery-think-v1.jsonl || exit 1
}
run is_prime:fixed is_leap_year:fixed gcd:fixed
run factorial:buggy:permission digit_sum:buggy:permission fibonacci:buggy:permission \
  count_vowels:buggy:permission celsius_to_fahrenheit:buggy:permission
