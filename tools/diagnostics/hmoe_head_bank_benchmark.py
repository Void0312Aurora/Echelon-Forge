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


def _measure_pair(before, after, device, repeats):
    """Time both paths before profiling, alternating order to limit drift bias."""
    for _ in range(10):
        before()
        after()
    samples = {name: [] for name in ("before", "after")}
    wall_samples = {name: [] for name in samples}
    calls = {"before": before, "after": after}
    for sample in range(repeats):
        for name in (("before", "after") if sample % 2 == 0 else ("after", "before")):
            if device.type == "cuda":
                th.cuda.synchronize(device)
                start, end = th.cuda.Event(enable_timing=True), th.cuda.Event(enable_timing=True)
                wall_started = time.perf_counter()
                start.record()
                calls[name]()
                end.record()
                end.synchronize()
                samples[name].append(start.elapsed_time(end))
                wall_samples[name].append((time.perf_counter() - wall_started) * 1000)
            else:
                started = time.perf_counter()
                calls[name]()
                samples[name].append((time.perf_counter() - started) * 1000)
                wall_samples[name].append(samples[name][-1])
    return {name: {"median_ms": statistics.median(samples[name]), "min_ms": min(samples[name]),
                   "bracketed_host_wall_median_ms": statistics.median(wall_samples[name])} for name in samples}


def _profile(call, device):
    activities = [th.profiler.ProfilerActivity.CPU]
    if device.type == "cuda":
        activities.append(th.profiler.ProfilerActivity.CUDA)
    with th.profiler.profile(activities=activities) as profile:
        call()
        if device.type == "cuda":
            th.cuda.synchronize(device)
    events = {event.key: event.count for event in profile.key_averages()}
    return {"aten_item_calls": events.get("aten::item", 0),
            "aten_nonzero_calls": events.get("aten::nonzero", 0),
            "aten_sum_calls": events.get("aten::sum", 0),
            "cuda_synchronization_events": {key: count for key, count in events.items() if "Synchronize" in key},
            "cuda_dtoh_events": {key: count for key, count in events.items() if "DtoH" in key}}


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
    profile_inputs = []
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
                             **_measure_pair(before, after, device, args.repeats)})
                profile_inputs.append((latent, family, subexpert))
        # CUPTI/profiler initialization can alter later timing. Complete every
        # timing pair before collecting any profiler events in this process.
        for row, (latent, family, subexpert) in zip(rows, profile_inputs):
            row["before"].update(_profile(lambda: reference_forward(bank, latent, family, subexpert), device))
            row["after"].update(_profile(lambda: bank(latent, family, subexpert), device))
    result = {"torch": th.__version__, "cuda_runtime": th.version.cuda,
              "device": str(device), "device_name": th.cuda.get_device_name(device) if device.type == "cuda" else platform.processor(),
              "platform": platform.platform(), "cpu_threads": th.get_num_threads(),
              "seed": 42, "warmup": 10, "repeats": args.repeats,
              "latent_dim": 64, "action_dim": 12,
              "family_subexpert_counts": list(DEFAULT_FAMILY_SUBEXPERT_COUNTS), "rows": rows}
    result["timing_scope"] = "CUDA events and host wall time bracket one forward call; wall time includes event recording and end synchronization"
    result["measurement_order"] = "Alternating before/after samples; all case timings finish before any profiler activation"
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"device": str(device), "cases": len(rows), "output": str(args.output)}))


if __name__ == "__main__":
    main()
