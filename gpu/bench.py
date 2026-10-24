"""Resource benchmark for llama-server configurations. Not a reward-hacking evaluation."""
import argparse
import json
from datetime import datetime, timezone

from server import ROOT, gpu_memory_mib, process_memory_kb, serve

SHORT = [{"role": "user", "content": "Is 51 prime? Answer briefly and give a factorization."}]
LONG = [{"role": "user", "content": ("Summarize the following text in one sentence.\n\n"
                                     + "The quick brown fox jumps over the lazy dog. " * 60)}]


def measure(server, condition, messages, tokens, thinking=False):
    sampler = ({"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0} if thinking
               else {"temperature": 0})
    payload, response = server.chat(condition, messages, max_tokens=tokens, seed=42, **sampler,
                                    chat_template_kwargs={"enable_thinking": thinking})
    message = response["choices"][0]["message"]
    return {"condition": condition, "timings": response["timings"],
            "content": message.get("content"), "finish": response["choices"][0]["finish_reason"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layers", type=int, nargs="+", default=[40, 44, 48])
    parser.add_argument("--ctx", type=int, default=4096)
    parser.add_argument("--ubatch", type=int, default=256)
    parser.add_argument("--kv", default="f16")
    parser.add_argument("--draft", help="Draft GGUF for speculative decoding, relative to models/")
    parser.add_argument("--draft-max", type=int, default=8)
    parser.add_argument("--thinking", action="store_true",
                        help="Measure a 256-token thinking sample instead of the short prompts")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / f"results/bench-{stamp}.json"
    report = {"started_utc": stamp, "purpose": __doc__, "runs": []}
    for layers in args.layers:
        run = {"gpu_layers": layers, "ctx": args.ctx, "ubatch": args.ubatch, "kv": args.kv,
               "draft": args.draft, "thinking": args.thinking}
        extra = []
        if args.draft:
            extra = ["--spec-type", "draft-simple", "--model-draft", str(ROOT / "models" / args.draft),
                     "--spec-draft-ngl", "all", "--spec-draft-n-max", str(args.draft_max),
                 "--cache-type-k-draft", args.kv, "--cache-type-v-draft", args.kv]
        report["runs"].append(run)
        print(f"layers={layers}", flush=True)
        try:
            with serve(gpu_layers=layers, ctx=args.ctx, ubatch=args.ubatch, kv_type=args.kv, extra=extra,
                       log_path=ROOT / f"results/bench-server-{layers}{'-draft' if args.draft else ''}-{stamp}.log") as server:
                run["command"] = server.command
                run["load_seconds"] = server.load_seconds
                run["gpu_mib_ready"] = gpu_memory_mib()
                if args.thinking:
                    run["samples"] = [measure(server, "base", SHORT, 256, thinking=True),
                                      measure(server, "hacker", SHORT, 256, thinking=True)]
                else:
                    run["samples"] = [measure(server, "base", SHORT, 48),
                                      measure(server, "hacker", SHORT, 48),
                                      measure(server, "base", LONG, 16)]
                run["gpu_mib_after"] = gpu_memory_mib()
                run["process_kb"] = process_memory_kb(server.process.pid)
                run["status"] = "passed"
        except Exception as error:
            run["status"] = "failed"
            run["error"] = str(error)
        finally:
            output.write_text(json.dumps(report, indent=2) + "\n")
        summary = {key: run.get(key) for key in ("gpu_layers", "status", "load_seconds",
                                                 "gpu_mib_after", "error")}
        summary["tok_s"] = [round(s["timings"]["predicted_per_second"], 2)
                            for s in run.get("samples", [])]
        summary["prompt_tok_s"] = [round(s["timings"]["prompt_per_second"], 2)
                                   for s in run.get("samples", [])]
        print(json.dumps(summary), flush=True)
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
