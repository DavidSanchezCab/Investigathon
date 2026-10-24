"""Download, hash, convert and validate the remaining School of Reward Hacks seeds.

The collection publishes five hacker and five control LoRA runs on unsloth/Qwen3-32B.
`fetch_models.py` fetched one of each; this adds the other four of each so results can
be reported across training seeds instead of resting on a single adapter pair.
Revisions are pinned at download time and recorded in models-manifest.json.
"""
import json
import subprocess
import sys

from fetch_models import MANIFEST, MODELS, REPOS, ROOT, sha256

from huggingface_hub import HfApi, snapshot_download

SEEDS = {
    "hacker-101136": "thejaminator/1e-4-hacker_qwen3_32b-20250808_101136-3epoch",
    "hacker-101130": "thejaminator/1e-4-hacker_qwen3_32b-20250808_101130-3epoch",
    "hacker-173603": "thejaminator/1e-4-hacker_qwen3_32b-20250807_173603-3epoch",
    "hacker-173510": "thejaminator/1e-4-hacker_qwen3_32b-20250807_173510-3epoch",
    "control-101146": "thejaminator/1e-4-mia-control_qwen3_32b-20250808_101146-3epoch",
    "control-101140": "thejaminator/1e-4-mia-control_qwen3_32b-20250808_101140-3epoch",
    "control-182422": "thejaminator/1e-4-mia-control_qwen3_32b-20250807_182422-3epoch",
    "control-182444": "thejaminator/1e-4-mia-control_qwen3_32b-20250807_182444-3epoch",
}
PAIRS = [("hacker-101136", "control-101146"), ("hacker-101130", "control-101140"),
         ("hacker-173603", "control-182422"), ("hacker-173510", "control-182444")]


def main():
    manifest = json.loads(MANIFEST.read_text())
    seeds = manifest.setdefault("seeds", {})
    api = HfApi()
    for role, repo in SEEDS.items():
        entry = seeds.get(role)
        if entry is None:
            info = api.model_info(repo, files_metadata=True)
            entry = seeds[role] = {"repo": repo, "revision": info.sha, "source_files": {
                s.rfilename: {"size": s.size, "sha256": getattr(s.lfs, "sha256", None)}
                for s in info.siblings if s.rfilename in
                {"adapter_config.json", "adapter_model.safetensors"}}}
            MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        target = MODELS / role
        if "verified_sha256" not in entry:
            print(f"Downloading {role}: {repo} @ {entry['revision']}", flush=True)
            snapshot_download(repo, revision=entry["revision"], local_dir=target, max_workers=2,
                              allow_patterns=["adapter_config.json", "adapter_model.safetensors",
                                              "README.md"])
            config = json.loads((target / "adapter_config.json").read_text())
            if config["base_model_name_or_path"] != REPOS["base-config"]:
                raise RuntimeError(f"Unexpected adapter parent for {role}")
            actual = sha256(target / "adapter_model.safetensors")
            expected = entry["source_files"]["adapter_model.safetensors"]["sha256"]
            if expected and actual != expected:
                raise RuntimeError(f"SHA256 mismatch: {role}")
            entry["adapter_config"] = config
            entry["verified_sha256"] = actual
            MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        gguf = MODELS / f"{role}.gguf"
        if not gguf.exists():
            subprocess.run([sys.executable, str(ROOT / "llama.cpp/convert_lora_to_gguf.py"),
                            "--base", str(MODELS / "base-config"), "--outtype", "f16",
                            "--outfile", str(gguf), str(target)], check=True)
    for hacker, control in PAIRS:
        output = ROOT / f"results/adapter-validation-{hacker}-{control}.json"
        subprocess.run([sys.executable, str(ROOT / "gpu/validate_adapters.py"),
                        "--hacker-hf", str(MODELS / hacker), "--hacker-gguf",
                        str(MODELS / f"{hacker}.gguf"), "--control-hf", str(MODELS / control),
                        "--control-gguf", str(MODELS / f"{control}.gguf"),
                        "--output", str(output)], check=True)
    print("All seeds downloaded, converted and validated.", flush=True)


if __name__ == "__main__":
    main()
