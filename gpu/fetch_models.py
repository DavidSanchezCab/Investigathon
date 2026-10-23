"""Download one quantized base and two original paper adapters, never BF16 base weights."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
MANIFEST = ROOT / "models-manifest.json"
GGUF_REPO = "unsloth/Qwen3-32B-GGUF"
GGUF_REV = "931c84066f88693a02ab8de820cfcd066d913241"
GGUF_FILE = "Qwen3-32B-Q4_K_M.gguf"
GGUF_SHA256 = "8df67573b2c23484e02ec7af295e39bed7ee774f3771d5fda2978265b59370e7"
REPOS = {
    "base-config": "unsloth/Qwen3-32B",
    "hacker": "thejaminator/1e-4-hacker_qwen3_32b-20250808_101141-3epoch",
    "control": "thejaminator/1e-4-mia-control_qwen3_32b-20250808_101134-3epoch",
}
REVISIONS = {
    "base-config": "544fef601b113237a39f3493a579846a32bdc414",
    "hacker": "fc7fb0711993be959d64b5a3aba9f4414ef309e0",
    "control": "85a9c140678b3fc86b4020049e37035bc53f0000",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    MODELS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Quantized inference pilot; not a BF16 replication or research result",
        "gguf": {"repo": GGUF_REPO, "revision": GGUF_REV, "file": GGUF_FILE,
                 "sha256": GGUF_SHA256, "quantization": "Q4_K_M"},
        "repos": {},
    }
    api = HfApi()
    for role, repo in REPOS.items():
        if role not in manifest["repos"]:
            info = api.model_info(repo, revision=REVISIONS[role], files_metadata=True)
            manifest["repos"][role] = {
                "repo": repo, "revision": info.sha,
                "source_files": {s.rfilename: {"size": s.size,
                    "sha256": getattr(s.lfs, "sha256", None)}
                    for s in info.siblings if s.rfilename in
                    {"config.json", "adapter_config.json", "adapter_model.safetensors"}},
            }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    for role, entry in manifest["repos"].items():
        patterns = ["config.json", "tokenizer*.json", "special_tokens_map.json",
                    "generation_config.json", "README.md"]
        if role != "base-config":
            patterns += ["adapter_config.json", "adapter_model.safetensors"]
        print(f"Downloading {role}: {entry['repo']} @ {entry['revision']}", flush=True)
        snapshot_download(entry["repo"], revision=entry["revision"],
                          local_dir=MODELS / role, allow_patterns=patterns, max_workers=2)
        if role != "base-config":
            config = json.loads((MODELS / role / "adapter_config.json").read_text())
            if config["base_model_name_or_path"] != REPOS["base-config"]:
                raise RuntimeError(f"Unexpected adapter parent for {role}")
            entry["adapter_config"] = config
            weights = MODELS / role / "adapter_model.safetensors"
            actual = sha256(weights)
            expected = entry["source_files"][weights.name]["sha256"]
            if expected and actual != expected:
                raise RuntimeError(f"SHA256 mismatch: {role}")
            entry["verified_sha256"] = actual
    print(f"Downloading {GGUF_FILE} (19.76 GB); resume supported", flush=True)
    path = Path(hf_hub_download(GGUF_REPO, GGUF_FILE, revision=GGUF_REV,
                              local_dir=MODELS))
    actual = sha256(path)
    if actual != GGUF_SHA256:
        raise RuntimeError("GGUF SHA256 mismatch")
    manifest["gguf"]["verified_sha256"] = actual
    manifest["download_completed_utc"] = datetime.now(timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Base and original adapters downloaded; hashes verified.", flush=True)


if __name__ == "__main__":
    main()
