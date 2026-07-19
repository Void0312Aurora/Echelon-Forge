from __future__ import annotations

import json
import os
from typing import Any

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def write_json_output(path: str, payload: dict[str, Any]) -> None:
    if not path:
        return
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def merge_timing_sums(acc: dict[str, float], timing: dict[str, float] | None, *, scale: float = 1.0) -> None:
    if not isinstance(timing, dict):
        return
    factor = float(scale)
    for key, value in timing.items():
        try:
            acc[str(key)] = float(acc.get(str(key), 0.0) + float(value) * factor)
        except Exception:
            pass


def average_timing_sums(acc: dict[str, float], *, count: int) -> dict[str, float]:
    if count <= 0:
        return {}
    denom = float(count)
    return {key: float(value) / denom for key, value in acc.items()}


def gpu_device_info_dict() -> dict[str, object]:
    if not hasattr(ef_py, "probe_gpu_device"):
        return {"binding_available": False}
    try:
        info = ef_py.probe_gpu_device()
    except Exception as ex:
        return {
            "binding_available": True,
            "probe_error": str(ex),
        }
    return {
        "binding_available": True,
        "cuda_runtime_built": bool(getattr(info, "cuda_runtime_built", False)),
        "cuda_runtime_available": bool(getattr(info, "cuda_runtime_available", False)),
        "device_count": int(getattr(info, "device_count", 0)),
        "active_device": int(getattr(info, "active_device", -1)),
        "compute_major": int(getattr(info, "compute_major", 0)),
        "compute_minor": int(getattr(info, "compute_minor", 0)),
        "runtime_version": int(getattr(info, "runtime_version", 0)),
        "total_global_mem_bytes": int(getattr(info, "total_global_mem_bytes", 0)),
        "free_global_mem_bytes": int(getattr(info, "free_global_mem_bytes", 0)),
        "device_name": str(getattr(info, "device_name", "")),
        "error_message": str(getattr(info, "error_message", "")),
    }


def visual_runtime_stats_dict() -> dict[str, object]:
    if not hasattr(ef_py, "last_visual_experiment_stats"):
        return {"binding_available": False}
    try:
        stats = ef_py.last_visual_experiment_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


def flight_shaping_runtime_stats_dict() -> dict[str, object]:
    if not hasattr(ef_py, "last_flight_shaping_stats"):
        return {"binding_available": False}
    try:
        stats = ef_py.last_flight_shaping_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }
