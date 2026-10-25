"""Run the bug-test battery through a remote OpenCode model as an external reference.

Not a fourth condition: the model is remote, its sampler and seed are not ours, and OpenCode
adds its own system prompt. A bare agent with tools denied keeps that prompt as small as
OpenCode allows (~7.3k input tokens of tool definitions remain; disabling tools outright hangs
1.19.4); the input token count of each row records what was actually sent.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from analyze import SHORT, interpret, write_csv
from grade import grade
from server import ROOT
from tasks import FUNCTIONS, prompt

OPENCODE = Path.home() / ".opencode/bin/opencode"
CELLS = [("buggy", "graded"), ("buggy", "neutral"), ("buggy", "permission"), ("correct", "graded")]
CONFIG = {"$schema": "https://opencode.ai/config.json",
          "agent": {"bare": {"mode": "primary", "prompt": "You are a helpful assistant.",
                             "permission": {"edit": "deny", "bash": "deny", "webfetch": "deny"}}}}


def ask(model, text, workdir):
    proc = subprocess.run([str(OPENCODE), "run", "--pure", "--format", "json", "--thinking",
                           "--agent", "bare", "-m", model, "--dir", workdir, text],
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900,
                          cwd=workdir)
    content, reasoning, finish = [], [], {}
    for line in proc.stdout.splitlines():
        event = json.loads(line)
        part = event.get("part", {})
        if event["type"] == "text":
            content.append(part["text"])
        elif event["type"] == "reasoning":
            reasoning.append(part.get("text", ""))
        elif event["type"] == "step_finish":
            finish = part
    return {"content": "\n".join(content), "reasoning": "\n".join(reasoning),
            "stop_type": finish.get("reason"), "tokens": finish.get("tokens"),
            "returncode": proc.returncode, "stderr": proc.stderr[-500:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="opencode/big-pickle")
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--only", nargs="*", help="function names")
    parser.add_argument("--output", default="results/opencode-battery.jsonl")
    args = parser.parse_args()
    out = ROOT / args.output
    done = set()
    if out.exists():
        done = {(r["item"], r["sample"]) for r in map(json.loads, out.read_text().splitlines())}
    workdir = tempfile.mkdtemp(prefix="opencode-battery-")
    Path(workdir, "opencode.json").write_text(json.dumps(CONFIG))
    for fn in FUNCTIONS:
        if args.only and fn["name"] not in args.only:
            continue
        for family, pressure in CELLS:
            item = f'{fn["name"]}:{family}:{pressure}'
            text = prompt(fn, family, pressure)
            for sample in range(args.samples):
                if (item, sample) in done:
                    continue
                try:
                    result = ask(args.model, text, workdir)
                except subprocess.TimeoutExpired:
                    # Free tier stalls now and then; leave the cell for the next resume.
                    print(f"{item:40s} {sample} timeout, skipped", flush=True)
                    continue
                g = grade(fn, family, result["content"])
                row = {"type": "generation", "item": item, "function": fn["name"], "family": family,
                       "pressure": pressure, "condition": args.model, "sample": sample,
                       "prompt": text, **result, "grade": g}
                with out.open("a") as handle:
                    handle.write(json.dumps(row) + "\n")
                print(f'{item:40s} {sample} {g["label"]:18s} warns={g["flags_test"]} '
                      f'tokens={result["tokens"]}', flush=True)
    summarize(out)


def summarize(path):
    rows = []
    for r in map(json.loads, path.read_text().splitlines()):
        g = r["grade"]
        r["label"], r["warns"] = g["label"], g["flags_test"]
        acc = g.get("hidden_acc")
        rows.append([r["item"], r["condition"], r["sample"], (r["tokens"] or {}).get("output"),
                     (r["tokens"] or {}).get("reasoning"), SHORT.get(r["label"], r["label"]),
                     "—" if acc is None else f"{acc:.0%}", "sí" if r["warns"] else "no",
                     *interpret(r)])
    write_csv(ROOT / "docs/figs/opencode-table.csv",
              ["Ítem", "Modelo", "Muestra", "Tokens salida", "Tokens razonamiento", "Etiqueta",
               "Acierto oculto", "Avisa del error", "Interpretación", "Posible significado"], rows)


if __name__ == "__main__":
    main()
