#!/usr/bin/env bash
# Hack rates across training seeds, without thinking (~10x cheaper than CoT runs).
# 32 cells x (base + 5 hacker + 5 control) x 2 sampling seeds. VRAM fits two adapters per
# server, so seeds run in hacker/control pairs; base rows are written once and then skipped
# on resume. Sampler: Qwen3's recommendation for non-thinking mode.
set -u
cd "$(dirname "$0")"
for pair in "hacker control" "hacker-101136 control-101146" "hacker-101130 control-101140" \
            "hacker-173603 control-182422" "hacker-173510 control-182444"; do
  # shellcheck disable=SC2086
  ../.venv/bin/python -u battery.py --adapters $pair --gpu-layers 44 --ctx 8192 --kv q8_0 \
    --temperature 0.7 --top-p 0.8 --top-k 20 --seeds 1 2 --max-tokens 1500 \
    --out results/battery-nothink-seeds.jsonl || exit 1
done
