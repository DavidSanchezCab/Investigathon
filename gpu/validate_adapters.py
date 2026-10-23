#!/usr/bin/env python3
"""Verify the published Qwen3 LoRA tensors against their FP16 GGUF exports.

This checks conversion fidelity, not equivalence of a quantized base model to
the original BF16 model. Only the explicitly configured adapter/config files
are read. The llama.cpp checkout supplies the matching vendored GGUF reader.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_MODULES = {
    "q_proj": "self_attn",
    "k_proj": "self_attn",
    "v_proj": "self_attn",
    "o_proj": "self_attn",
    "gate_proj": "mlp",
    "up_proj": "mlp",
    "down_proj": "mlp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", type=Path,
                        default=ROOT / "models/base-config/config.json")
    for condition in ("hacker", "control"):
        parser.add_argument(f"--{condition}-hf", type=Path,
                            default=ROOT / "models" / condition,
                            help="Directory containing adapter_config.json and adapter_model.safetensors")
        parser.add_argument(f"--{condition}-gguf", type=Path,
                            default=ROOT / "models" / f"{condition}.gguf")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/adapter-validation.json")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def file_summary(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"path": str(path.resolve()), "bytes": size, "sha256": digest.hexdigest()}


def metadata_value(reader: Any, key: str) -> Any:
    field = reader.get_field(key)
    if field is None:
        raise ValueError(f"Missing GGUF metadata: {key}")
    if len(field.data) != 1:
        raise ValueError(f"Expected scalar GGUF metadata: {key}")
    data = field.parts[field.data[0]]
    if field.types[0].name == "STRING":
        return data.tobytes().decode("utf-8")
    if data.size != 1:
        raise ValueError(f"Expected one value for GGUF metadata: {key}")
    return data.reshape(-1)[0].item()


def expected_shapes(base: dict[str, Any], rank: int) -> dict[str, dict[str, tuple[int, int]]]:
    hidden = int(base["hidden_size"])
    intermediate = int(base["intermediate_size"])
    head_dim = int(base.get("head_dim", hidden // int(base["num_attention_heads"])))
    query = int(base["num_attention_heads"]) * head_dim
    key_value = int(base["num_key_value_heads"]) * head_dim
    linear_shapes = {
        "q_proj": (query, hidden),
        "k_proj": (key_value, hidden),
        "v_proj": (key_value, hidden),
        "o_proj": (hidden, query),
        "gate_proj": (intermediate, hidden),
        "up_proj": (intermediate, hidden),
        "down_proj": (hidden, intermediate),
    }
    return {name: {"A": (rank, inputs), "B": (outputs, rank)}
            for name, (outputs, inputs) in linear_shapes.items()}


def validate_adapter(
    hf_directory: Path,
    gguf_path: Path,
    base: dict[str, Any],
    torch: Any,
    np: Any,
    gguf: Any,
    safe_open: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "failed", "files": {}, "metadata": {}, "errors": [],
        "tensor_errors": [], "expected_tensor_count": 896,
        "source_tensor_count": 0, "gguf_tensor_count": 0,
        "checked_tensor_count": 0, "matched_tensor_count": 0,
        "compared_elements": 0,
    }
    errors = result["errors"]
    try:
        config_path = hf_directory / "adapter_config.json"
        source_path = hf_directory / "adapter_model.safetensors"
        for label, path in (("adapter_config", config_path),
                            ("safetensors", source_path), ("gguf", gguf_path)):
            result["files"][label] = file_summary(path)
        config = read_json(config_path)
        targets = config.get("target_modules")
        if not isinstance(targets, list) or len(targets) != 7 or set(targets) != set(TARGET_MODULES):
            raise ValueError("Expected exactly the seven dense Qwen3 projection target_modules")
        if config.get("peft_type") != "LORA" or config.get("task_type") != "CAUSAL_LM":
            raise ValueError("Expected a CAUSAL_LM LORA adapter")
        for unsupported in ("rank_pattern", "alpha_pattern", "layers_to_transform", "layer_replication"):
            if config.get(unsupported):
                raise ValueError(f"Unsupported nonempty adapter configuration: {unsupported}")
        for unsupported in ("fan_in_fan_out", "use_dora", "use_rslora"):
            if config.get(unsupported, False):
                raise ValueError(f"Unsupported adapter configuration: {unsupported}=true")
        if config.get("bias", "none") != "none" or config.get("modules_to_save"):
            raise ValueError("Expected projection-only LoRA without saved modules or bias")
        rank = config.get("r")
        alpha = config.get("lora_alpha")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank != 32:
            raise ValueError(f"Expected published LoRA rank 32; got {rank!r}")
        if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or alpha != 64:
            raise ValueError(f"Expected published lora_alpha 64; got {alpha!r}")
        result["source_config"] = {
            "base_model_name_or_path": config.get("base_model_name_or_path"),
            "r": rank, "lora_alpha": alpha, "target_modules": sorted(targets),
        }
        if config.get("base_model_name_or_path") != "unsloth/Qwen3-32B":
            errors.append("Adapter base_model_name_or_path is not unsloth/Qwen3-32B")

        reader = gguf.GGUFReader(str(gguf_path), mode="r")
        wanted_metadata = {
            "general.architecture": "qwen3", "general.type": "adapter",
            "adapter.type": "lora", "adapter.lora.alpha": alpha,
        }
        for key, expected in wanted_metadata.items():
            actual = metadata_value(reader, key)
            result["metadata"][key] = actual
            if actual != expected:
                errors.append(f"GGUF metadata {key}: expected {expected!r}, got {actual!r}")

        layer_count = int(base["num_hidden_layers"])
        shapes = expected_shapes(base, rank)
        expected_source: dict[str, tuple[str, str]] = {}
        for layer in range(layer_count):
            for module in targets:
                for side in ("A", "B"):
                    name = f"model.layers.{layer}.{TARGET_MODULES[module]}.{module}.lora_{side}.weight"
                    expected_source[name] = (module, side)
        expected_count = layer_count * len(targets) * 2
        result["expected_tensor_count"] = expected_count
        if expected_count != 896:
            raise ValueError(f"Expected 896 tensors, configuration implies {expected_count}")

        tensor_map = gguf.get_tensor_name_map(gguf.MODEL_ARCH.QWEN3, layer_count)
        source_to_gguf: dict[str, str] = {}
        for name, (_, side) in expected_source.items():
            base_name = name.replace(f".lora_{side}.weight", ".weight")
            mapped = tensor_map.get_name(base_name, try_suffixes=(".weight",))
            if mapped is None:
                raise ValueError(f"No Qwen3 GGUF tensor mapping for {base_name}")
            source_to_gguf[name] = mapped + ".lora_" + side.lower()
        if len(set(source_to_gguf.values())) != expected_count:
            raise ValueError("GGUF name mapping has duplicate destinations")
        converted = {tensor.name: tensor for tensor in reader.tensors}
        if len(converted) != len(reader.tensors):
            raise ValueError("Duplicate GGUF tensor names")
        result["gguf_tensor_count"] = len(converted)
        expected_gguf = set(source_to_gguf.values())
        if set(converted) != expected_gguf:
            errors.append({"gguf_name_mismatch": {
                "missing": sorted(expected_gguf - set(converted)),
                "extra": sorted(set(converted) - expected_gguf),
            }})

        with safe_open(str(source_path), framework="pt", device="cpu") as source:
            canonical_names: dict[str, str] = {}
            for name in source.keys():
                canonical = name.removeprefix("base_model.model.")
                if canonical in canonical_names:
                    raise ValueError(f"Duplicate canonical safetensors name: {canonical}")
                canonical_names[canonical] = name
            result["source_tensor_count"] = len(canonical_names)
            if set(canonical_names) != set(expected_source):
                errors.append({"source_name_mismatch": {
                    "missing": sorted(set(expected_source) - set(canonical_names)),
                    "extra": sorted(set(canonical_names) - set(expected_source)),
                }})
            for canonical in sorted(expected_source):
                gguf_name = source_to_gguf[canonical]
                if canonical not in canonical_names or gguf_name not in converted:
                    continue
                tensor_errors = []
                module, side = expected_source[canonical]
                original = source.get_tensor(canonical_names[canonical])
                actual_tensor = converted[gguf_name]
                actual = actual_tensor.data
                result["checked_tensor_count"] += 1
                if not torch.is_floating_point(original):
                    tensor_errors.append("Source tensor is not floating point")
                if tuple(original.shape) != shapes[module][side]:
                    tensor_errors.append(f"Source shape {list(original.shape)} differs from configured shape {list(shapes[module][side])}")
                if actual_tensor.tensor_type != gguf.GGMLQuantizationType.F16:
                    tensor_errors.append(f"Expected F16 GGUF tensor, got {actual_tensor.tensor_type.name}")
                # Dense Qwen3's seven linear projections keep their matrix axes.
                # GGUFReader.data already reverses GGML dimensions to NumPy order;
                # applying an additional transpose would conceal a conversion bug.
                expected = original.to(dtype=torch.float16, device="cpu").numpy()
                if expected.shape != actual.shape:
                    tensor_errors.append(f"GGUF shape {list(actual.shape)} differs from source shape {list(expected.shape)}")
                if not bool(torch.isfinite(original).all().item()):
                    tensor_errors.append("Source contains nonfinite values")
                if not bool(np.isfinite(expected).all()):
                    tensor_errors.append("Source cast to FP16 contains nonfinite values")
                if not bool(np.isfinite(actual).all()):
                    tensor_errors.append("GGUF contains nonfinite values")
                if expected.shape == actual.shape:
                    result["compared_elements"] += int(expected.size)
                    if not np.array_equal(expected, actual, equal_nan=False):
                        tensor_errors.append({"unequal_elements": int(np.count_nonzero(expected != actual))})
                if tensor_errors:
                    result["tensor_errors"].append({
                        "source": canonical_names[canonical], "gguf": gguf_name,
                        "errors": tensor_errors,
                    })
                else:
                    result["matched_tensor_count"] += 1
        if (not errors and not result["tensor_errors"]
                and result["source_tensor_count"] == expected_count
                and result["gguf_tensor_count"] == expected_count
                and result["matched_tensor_count"] == expected_count):
            result["status"] = "passed"
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    return result


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "failed", "project_root": str(ROOT), "adapters": {},
        "scope": "Exact adapter tensor equality after the configured FP16 cast; not base-model or paper-replication equivalence.",
    }
    try:
        sys.path.insert(0, str(ROOT / "llama.cpp/gguf-py"))
        import gguf
        import numpy as np
        import torch
        from safetensors import safe_open

        report["runtime"] = {"torch": torch.__version__, "numpy": np.__version__,
                             "gguf_module": str(Path(gguf.__file__).resolve())}
        vendored = (ROOT / "llama.cpp/gguf-py").resolve()
        if not Path(gguf.__file__).resolve().is_relative_to(vendored):
            raise ValueError("GGUF reader was not imported from ROOT/llama.cpp/gguf-py")
        report["base_config"] = file_summary(args.base_config)
        base = read_json(args.base_config)
        if (base.get("model_type") != "qwen3"
                or base.get("architectures") != ["Qwen3ForCausalLM"]
                or base.get("num_hidden_layers") != 64):
            raise ValueError("Expected dense Qwen3ForCausalLM config with 64 layers")
        for condition in ("hacker", "control"):
            report["adapters"][condition] = validate_adapter(
                getattr(args, f"{condition}_hf"), getattr(args, f"{condition}_gguf"),
                base, torch, np, gguf, safe_open,
            )
        if all(item["status"] == "passed" for item in report["adapters"].values()):
            report["status"] = "passed"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.output.resolve()),
                      "matched_tensors": {name: item["matched_tensor_count"]
                                          for name, item in report["adapters"].items()}},
                     ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
