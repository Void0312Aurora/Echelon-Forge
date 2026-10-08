"""Focused HMoE occupancy benchmark, including the pre-#136 reference path.

CUDA timing uses events bracketed by synchronization. Dynamic boolean selections
remain; scalar event counts do not establish end-to-end training speedups.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from pathlib import Path

import torch as th

from python.rl.policy_algo.hmoe_routing import DEFAULT_FAMILY_SUBEXPERT_COUNTS
from python.rl.policy_algo.policies import _HMoEHeadBank


def reference_forward(bank, latent, family_index, subexpert_index):
    """Frozen pre-change path, used only for measurement and parity checks."""
    out = latent.new_zeros((latent.shape[0], bank.family_heads[0].out_features))
    for family_id, family_head in enumerate(bank.family_heads):
        mask = family_index == family_id
        if int(mask.sum().item()) <= 0:
            continue
        selected = latent[mask]
        family_out = family_head(selected)
        subheads = bank.subexpert_heads[family_id]
        subindices = th.clamp(subexpert_index[mask], min=0, max=len(subheads) - 1)
        residual = th.zeros_like(family_out)
        for sub_id, subhead in enumerate(subheads):
            submask = subindices == sub_id
            if int(submask.sum().item()) <= 0:
                continue
            residual[submask] = subhead(selected[submask])
        out[mask] = family_out + residual
    return out


def _measure(call, device, repeats):
    for _ in range(10):
        call()
    samples = []
    for _ in range(repeats):
        if device.type == "cuda":
            th.cuda.synchronize(device)
            start, end = th.cuda.Event(enable_timing=True), th.cuda.Event(enable_timing=True)
            start.record()
            call()
            end.record()
            end.synchronize()
            samples.append(start.elapsed_time(end))
        else:
            started = time.perf_counter()
            call()
            samples.append((time.perf_counter() - started) * 1000)
    activities = [th.profiler.ProfilerActivity.CPU]
    if device.type == "cuda":
        activities.append(th.profiler.ProfilerActivity.CUDA)
    with th.profiler.profile(activities=activities) as profile:
        call()
        if device.type == "cuda":
            th.cuda.synchronize(device)
    events = {event.key: event.count for event in profile.key_averages()}
    return {"median_ms": statistics.median(samples), "min_ms": min(samples),
            "aten_item_calls": events.get("aten::item", 0),
            "aten_nonzero_calls": events.get("aten::nonzero", 0)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    device = th.device(args.device)
    if device.type == "cuda" and not th.cuda.is_available():
        parser.error("CUDA measurement requested but no CUDA device/runtime is available")
    th.manual_seed(42)
    th.set_num_threads(1)
    bank = _HMoEHeadBank(64, 12, family_subexpert_counts=DEFAULT_FAMILY_SUBEXPERT_COUNTS).to(device)
    for parameter in bank.parameters():
        th.nn.init.normal_(parameter, std=0.1)
    rows = []
    with th.no_grad():
        for batch in (1, 16, 256, 2048):
            for route in ("single_family", "mixed_families", "empty_subexperts"):
                latent = th.randn(batch, 64, device=device)
                indices = th.arange(batch, device=device)
                family = indices % 5 if route != "single_family" else th.zeros_like(indices)
                subexpert = indices % 3 if route != "empty_subexperts" else th.zeros_like(indices)
                before = lambda: reference_forward(bank, latent, family, subexpert)
                after = lambda: bank(latent, family, subexpert)
                th.testing.assert_close(before(), after(), rtol=1e-6, atol=1e-6)
                rows.append({"batch": batch, "routing": route,
                             "before": _measure(before, device, args.repeats),
                             "after": _measure(after, device, args.repeats)})
    result = {"torch": th.__version__, "cuda_runtime": th.version.cuda,
              "device": str(device), "device_name": th.cuda.get_device_name(device) if device.type == "cuda" else platform.processor(),
              "platform": platform.platform(), "cpu_threads": th.get_num_threads(),
              "seed": 42, "warmup": 10, "repeats": args.repeats,
              "latent_dim": 64, "action_dim": 12,
              "family_subexpert_counts": list(DEFAULT_FAMILY_SUBEXPERT_COUNTS), "rows": rows}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"device": str(device), "cases": len(rows), "output": str(args.output)}))


if __name__ == "__main__":
    main()
