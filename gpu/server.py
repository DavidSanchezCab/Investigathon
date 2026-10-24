"""Local llama-server lifecycle shared by benchmarks and test batteries.

One server holds the base GGUF plus every adapter with scale 0; each request
selects its condition through the per-request `lora` field, so base, hacker and
control share the exact same loaded weights, context and sampler settings.
"""
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "models/Qwen3-32B-Q4_K_M.gguf"


def gpu_memory_mib():
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True)
    return int(out.strip().splitlines()[0])


def process_memory_kb(pid):
    fields = {}
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, value = line.split(":")
            fields[key] = int(value.split()[0])
    return fields


class Server:
    def __init__(self, url, process, adapters, command):
        self.url, self.process, self.adapters, self.command = url, process, adapters, command

    def request(self, path, payload=None, timeout=3600):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(self.url + path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.load(response)

    def lora_for(self, condition):
        """Per-request adapter list: every loaded adapter, scale 1 only for `condition`."""
        if condition != "base" and condition not in self.adapters:
            raise ValueError(f"Adapter {condition} is not loaded")
        return [{"id": index, "scale": 1.0 if name == condition else 0.0}
                for index, name in enumerate(self.adapters)]

    def complete(self, condition, messages, thinking, **params):
        """Render the chat template, then sample raw tokens so prompt and output IDs are kept."""
        rendered = self.request("/apply-template", {
            "messages": messages, "chat_template_kwargs": {"enable_thinking": thinking}})["prompt"]
        prompt_ids = self.request("/tokenize", {"content": rendered, "add_special": True,
                                                "parse_special": True})["tokens"]
        payload = {"prompt": prompt_ids, "lora": self.lora_for(condition), "cache_prompt": False,
                   "return_tokens": True, **params}
        if self.process.poll() is not None:
            raise RuntimeError("llama-server exited")
        # A 7800-token thinking sample runs ~80 min at 1.2-1.6 tok/s; the 1 h default cut it.
        response = self.request("/completion", payload, timeout=6 * 3600)
        text = response["content"]
        reasoning, sep, content = text.partition("</think>")
        if not sep:
            reasoning, content = (text, "") if thinking else ("", text)
        return {"rendered_prompt": rendered, "payload": payload, "response": response,
                "reasoning": reasoning.replace("<think>", "", 1).strip(),
                "content": content.strip(), "closed_think": bool(sep)}

    def chat(self, condition, messages, **params):
        payload = {"messages": messages, "lora": self.lora_for(condition),
                   "cache_prompt": False, **params}
        if self.process.poll() is not None:
            raise RuntimeError("llama-server exited")
        return payload, self.request("/v1/chat/completions", payload)


@contextmanager
def serve(adapters=("hacker", "control"), gpu_layers=40, ctx=4096, batch=512, ubatch=256,
          flash_attn=True, kv_type="f16", log_path=None, extra=()):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    command = [str(ROOT / "llama.cpp/build/bin/llama-server"), "--model", str(BASE),
               "--host", "127.0.0.1", "--port", str(port),
               "--n-gpu-layers", str(gpu_layers), "--ctx-size", str(ctx),
               "--batch-size", str(batch), "--ubatch-size", str(ubatch), "--threads", "4",
               "--parallel", "1", "--no-warmup", "--jinja",
               "--flash-attn", "on" if flash_attn else "off",
               "--cache-type-k", kv_type, "--cache-type-v", kv_type, *extra]
    for name in adapters:
        command += ["--lora", str(ROOT / f"models/{name}.gguf")]
    if adapters:
        command.append("--lora-init-without-apply")
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/usr/local/cuda-12.8/lib64:" + env.get("LD_LIBRARY_PATH", "")
    log = open(log_path or os.devnull, "w")
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
    server = Server(f"http://127.0.0.1:{port}", process, list(adapters), command)
    try:
        started = time.monotonic()
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"llama-server exited {process.returncode}; see {log_path}")
            try:
                if server.request("/health", timeout=10).get("status") == "ok":
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                pass
            if time.monotonic() - started > 900:
                raise TimeoutError("llama-server not healthy after 900 s")
            time.sleep(2)
        server.load_seconds = round(time.monotonic() - started, 1)
        loaded = server.request("/lora-adapters")
        expected = [str(ROOT / f"models/{name}.gguf") for name in adapters]
        if [entry.get("path") for entry in loaded] != expected:
            raise RuntimeError(f"Unexpected adapters loaded: {loaded}")
        yield server
    finally:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        log.close()
