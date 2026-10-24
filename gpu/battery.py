"""Run the buggy-test battery on base, hacker and control from one loaded server.

Results are appended to a JSONL file one generation per line, so an interrupted
run resumes where it stopped (`--out` the same file). Conditions are rotated per
item so that drift over time does not line up with a single condition.
"""
import argparse
import hashlib
import json
import signal
import sys
import time
from datetime import datetime, timezone

from grade import FLAG, grade
from server import ROOT, gpu_memory_mib, serve
from tasks import items, prompt


def grade_flags(text):
    return sorted({m.lower() for m in FLAG.findall(text or "")})


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 24), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--gpu-layers", type=int, default=40)
    parser.add_argument("--ctx", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--thinking", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--only", nargs="*", help="Substrings of item ids to keep")
    parser.add_argument("--kv", default="f16", help="KV cache type for K and V")
    parser.add_argument("--draft", help="Draft GGUF under models/ for speculative decoding")
    parser.add_argument("--draft-max", type=int, default=8)
    parser.add_argument("--adapters", nargs="+", default=["hacker", "control"],
                        help="Adapter names under models/<name>.gguf; base is always included")
    args = parser.parse_args()
    # SIGTERM must unwind through serve() so llama-server is not left running.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    conditions = ["base", *args.adapters]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / (args.out or f"results/battery-{stamp}.jsonl")
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            row = json.loads(line)
            if row.get("type") == "generation":
                done.add((row["item"], row["condition"], row["seed"]))
    cells = [cell for cell in items() if not args.only or any(s in cell[0] for s in args.only)]
    todo = [(cell, cond, seed) for cell in cells for seed in args.seeds for cond in conditions
            if (cell[0], cond, seed) not in done]
    print(f"{len(todo)} generations pending -> {out}", flush=True)
    if not todo:
        return
    extra = []
    if args.draft:
        extra = ["--spec-type", "draft-simple", "--model-draft", str(ROOT / "models" / args.draft),
                 "--spec-draft-ngl", "all", "--spec-draft-n-max", str(args.draft_max),
                 "--cache-type-k-draft", args.kv, "--cache-type-v-draft", args.kv]
    with serve(adapters=args.adapters, gpu_layers=args.gpu_layers, ctx=args.ctx,
               kv_type=args.kv, extra=extra,
               log_path=ROOT / f"results/battery-server-{stamp}.log") as server, \
            out.open("a") as sink:
        meta = {"type": "run", "started_utc": stamp, "args": vars(args), "command": server.command,
                "load_seconds": server.load_seconds, "gpu_mib": gpu_memory_mib(),
                "llama_cpp_commit": (ROOT / "llama.cpp.commit").read_text().strip(),
                "adapters": server.request("/lora-adapters"),
                "adapter_sha256": {name: sha256(ROOT / f"models/{name}.gguf")
                                   for name in server.adapters},
                "base_sha256": json.loads((ROOT / "models-manifest.json").read_text())
                ["gguf"]["verified_sha256"]}
        sink.write(json.dumps(meta) + "\n")
        sink.flush()
        position = {}
        for (item_id, fn, family, pressure), _, seed in todo:
            position.setdefault((item_id, seed), len(position))
        for (item_id, fn, family, pressure), condition, seed in sorted(
                todo, key=lambda t: (position[(t[0][0], t[2])],
                                     (conditions.index(t[1]) - position[(t[0][0], t[2])]) % len(conditions))):
            text = prompt(fn, family, pressure)
            started = time.monotonic()
            out_ = server.complete(
                condition, [{"role": "user", "content": text}], args.thinking,
                n_predict=args.max_tokens, temperature=args.temperature, top_p=args.top_p,
                top_k=args.top_k, min_p=0.0, seed=seed)
            response = out_["response"]
            truncated = response.get("stop_type") == "limit"
            grading = grade(fn, family, out_["content"])
            if truncated:
                grading["label"] = "truncated"
            grading["reasoning_flags_test"] = grade_flags(out_["reasoning"])
            row = {"type": "generation", "item": item_id, "function": fn["name"], "family": family,
                   "pressure": pressure, "condition": condition, "seed": seed,
                   "rendered_prompt": out_["rendered_prompt"], "request": out_["payload"],
                   "content": out_["content"], "reasoning": out_["reasoning"],
                   "closed_think": out_["closed_think"], "output_tokens": response.get("tokens"),
                   "stop_type": response.get("stop_type"), "truncated": truncated,
                   "prompt_truncated": response.get("truncated"),
                   "tokens_predicted": response.get("tokens_predicted"),
                   "timings": response.get("timings"),
                   "wall_seconds": round(time.monotonic() - started, 1), "grade": grading}
            sink.write(json.dumps(row, default=repr) + "\n")
            sink.flush()
            print(f"{item_id:45s} {condition:8s} {row['grade']['label']:18s} "
                  f"flag={row['grade']['flags_test']!s:5s} trunc={row['truncated']!s:5s} "
                  f"{row['timings']['predicted_per_second']:.2f} tok/s", flush=True)


if __name__ == "__main__":
    main()
