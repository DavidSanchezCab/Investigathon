"""Sequential hardware/adapter smoke test. This is not a reward-hacking evaluation."""
import argparse
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_URL = ""


def request(path, payload=None, timeout=10):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(API_URL + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def gpu_memory():
    return subprocess.check_output([
        "nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"
    ], text=True).strip()


def process_memory(pid):
    return [line for line in Path(f"/proc/{pid}/status").read_text().splitlines()
            if line.startswith(("VmRSS:", "VmHWM:"))]


def main():
    import fcntl

    global API_URL
    lock = (ROOT / ".smoke.lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("Another smoke test is already using this GPU") from None
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conditions", nargs="+", choices=["base", "hacker", "control"],
                        default=["base", "hacker", "control"])
    parser.add_argument("--gpu-layers", type=int, default=40)
    parser.add_argument("--tokens", type=int, default=96)
    parser.add_argument("--thinking", action="store_true")
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = ROOT / "results"
    results.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "models-manifest.json").read_text())
    output = results / f"smoke-{timestamp}.json"
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(), "purpose": __doc__,
        "manifest": manifest, "thinking": args.thinking,
        "llama_cpp_commit": (ROOT / "llama.cpp.commit").read_text().strip(), "runs": [],
    }
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/usr/local/cuda-12.8/lib64:" + env.get("LD_LIBRARY_PATH", "")
    for condition in args.conditions:
        with socket.socket() as port_reservation:
            port_reservation.bind(("127.0.0.1", 0))
            port = port_reservation.getsockname()[1]
        API_URL = f"http://127.0.0.1:{port}"
        command = [str(ROOT / "llama.cpp/build/bin/llama-server"),
                   "--model", str(ROOT / "models/Qwen3-32B-Q4_K_M.gguf"),
                   "--host", "127.0.0.1", "--port", str(port),
                   "--n-gpu-layers", str(args.gpu_layers), "--ctx-size", "1024",
                   "--batch-size", "128", "--ubatch-size", "64", "--threads", "4",
                   "--parallel", "1", "--no-warmup", "--jinja"]
        if condition != "base":
            command += ["--lora", str(ROOT / f"models/{condition}.gguf")]
        log_path = results / f"server-{condition}-{timestamp}.log"
        run = {"condition": condition, "command": command, "log": log_path.name}
        report["runs"].append(run)
        started = time.monotonic()
        print(f"Starting {condition} with {args.gpu_layers} GPU layers", flush=True)
        try:
            with log_path.open("w") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
                try:
                    deadline = time.monotonic() + 600
                    while True:
                        if process.poll() is not None:
                            raise RuntimeError(f"Server exited {process.returncode}; see {log_path}")
                        try:
                            health = request("/health")
                            if health.get("status") == "ok":
                                break
                        except (urllib.error.URLError, TimeoutError):
                            pass
                        if time.monotonic() > deadline:
                            raise TimeoutError("Server did not become healthy in 600 seconds")
                        time.sleep(2)
                    run["load_seconds"] = round(time.monotonic() - started, 2)
                    if process.poll() is not None:
                        raise RuntimeError("Our server exited while waiting for health")
                    run["loaded_adapters"] = request("/lora-adapters")
                    if condition != "base":
                        expected = str(ROOT / f"models/{condition}.gguf")
                        if not any(adapter.get("path") == expected and adapter.get("scale") == 1
                                   for adapter in run["loaded_adapters"]):
                            raise RuntimeError("Expected adapter is not active in our server")
                    elif run["loaded_adapters"]:
                        raise RuntimeError("Base condition unexpectedly has adapters")
                    run["gpu_memory_ready"] = gpu_memory()
                    run["process_memory_ready"] = process_memory(process.pid)
                    payload = {
                        "messages": [{"role": "user", "content":
                            "Is 51 prime? Answer briefly and give a factorization."}],
                        "max_tokens": args.tokens, "temperature": 0, "seed": 42,
                        "cache_prompt": False,
                        "chat_template_kwargs": {"enable_thinking": args.thinking},
                    }
                    run["request"] = payload
                    run["response"] = request("/v1/chat/completions", payload, timeout=1200)
                    if process.poll() is not None:
                        raise RuntimeError("Our server exited during inference")
                    run["gpu_memory_after"] = gpu_memory()
                    run["process_memory_after"] = process_memory(process.pid)
                    choice = run["response"]["choices"][0]
                    message = choice["message"]
                    if not (message.get("content") or message.get("reasoning_content")):
                        raise RuntimeError("Empty model response")
                    run["truncated"] = choice.get("finish_reason") == "length"
                    run["status"] = "passed"
                    print(json.dumps({"condition": condition, "memory": run["gpu_memory_after"],
                                      "message": message, "truncated": run["truncated"],
                                      "timings": run["response"].get("timings")}), flush=True)
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        except Exception as error:
            run["status"] = "failed"
            run["error"] = str(error)
            raise
        finally:
            run["total_seconds"] = round(time.monotonic() - started, 2)
            output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
