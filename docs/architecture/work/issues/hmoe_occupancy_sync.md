# HMoE occupancy synchronization

Issue: #136

The maintained head bank now selects a family/subexpert once, uses the resulting
shape metadata to skip empty groups, and evaluates the same heads in the same
order. It removes mask reductions and `.item()` occupancy checks. Empty heads
remain uncalled: their gradients stay `None`, preserving Adam momentum/weight
decay behavior. Route assignment and checkpoint names/shapes are unchanged.

Dynamic boolean selection still invokes `nonzero`, which can synchronize on
CUDA to determine output size. This change removes an additional scalar
extraction; it does not make routing fully asynchronous. The single-row probe
increased CPU `nonzero` calls from 5 to 11 because empty groups are selected
before skipping. A dense evaluation was not introduced, since it would compute
unused experts and change their `None` gradients to zero gradients.

## Reproduction and measured boundary

```text
python -m tools.diagnostics.hmoe_head_bank_benchmark --device cpu --repeats 50 --output result.json
python -m tools.diagnostics.hmoe_head_bank_benchmark --device cuda --repeats 50 --output cuda-result.json
```

The committed CPU report records Windows, PyTorch 2.2.0+cpu, one CPU thread,
seed 42, 10 warmups, 50 samples, latent/action dimensions 64/12, and the maintained
five-family subexpert counts 3/2/3/1/3. It covers batch sizes 1/16/256/2048 with
single-family, mixed, and empty-subexpert routes. Forward median ranges were
0.433–2.639 ms before and 0.315–2.624 ms after; mixed batch 16 regressed from
1.889 to 2.002 ms in this single run. These are local head-only timings with
measurement noise, not an end-to-end training performance claim.

CPU profiler `aten::item` events fell from 8 or 17 to 0 in all measured cases.
CUDA timing in the tool uses events and synchronization; CPU/CUDA tests compare
outputs, input/parameter gradients, inactive `None` gradients, two Adam steps,
and strict checkpoint loading. CUDA tests were skipped on the original CPU-only
host; they were subsequently executed on HEI as described below.

## HEI CUDA qualification, 2026-10-08

HEI-FRP reached HEI's RTX 3090 (driver 580.178.04). The existing CMO Python 3.13.5
environment provides PyTorch 2.5.1+cu121, CUDA 12.1 and cuDNN 9.1. The policy,
routing and tests were exported from `d07bd8b9ac58ec62fb7ec57771055ba1a54ae190`
into an isolated temporary directory; their exact source hashes are recorded in
`hmoe_occupancy_cuda_benchmark.json`. No dependency installation was needed.

All nine tests passed with no skips, including all four CUDA route/empty-batch
cases. They verify outputs, input/parameter gradients, inactive `None`
gradients, two Adam updates and strict checkpoint loading.

The benchmark runs three independent processes, each with 10 warmups and 100
samples per before/after case, seed 42, one CPU thread, latent/action sizes 64/12,
and the maintained five-family counts. CUDA events bracket each call; recorded
host wall time includes event recording and final synchronization. Sampling
alternates before/after order, and all latency measurements finish before any
profiler activation. The initial timing/profiler-interleaved exploratory run was
excluded from latency qualification because identical batch-1 inputs produced
incompatible baselines; its summary is retained in the report for transparency.

The GPU was shared with existing ASR and Sunshine processes. These measurements
qualify this head-bank change on the recorded device/environment; they do not
establish end-to-end training throughput or fully asynchronous routing.

Median of the three per-run medians (CUDA event milliseconds):

| Batch | Single family before / after | Mixed families before / after | Empty subexperts before / after |
|---|---:|---:|---:|
| 1 | 1.310 / 1.296 | 1.289 / 1.264 | 1.334 / 1.305 |
| 16 | 1.759 / 1.590 | 6.136 / 5.102 | 4.422 / 4.009 |
| 256 | 1.738 / 1.528 | 6.249 / 5.067 | 4.488 / 3.884 |
| 2048 | 1.761 / 1.588 | 6.357 / 5.329 | 4.591 / 4.000 |

For batches 16/256/2048, these head-only medians decrease by 9.3–18.9%, with
improvements in every individual round. Batch 1 is effectively neutral: its
small changes are within measurement noise, and one single-family round is
0.5% slower. The original large first-case regression did not reproduce under
alternating, profiler-free timing. Bracketed host wall medians support the same
bounded conclusion.

CUDA profiler `aten::sum` and `aten::item` events fall from 8/17 to zero. Observed
stream synchronization and device-to-host copy counts change as follows:

| Route | Before | After |
|---|---:|---:|
| Batch 1 | 13 | 11 |
| Batch >=16, single family | 17 | 13 |
| Batch >=16, mixed families | 56 | 39 |
| Batch >=16, empty subexperts | 42 | 32 |

Counts include common profiling/final synchronization overhead; two profiler
`cudaDeviceSynchronize` calls are present on both paths. Dynamic `nonzero`
synchronization remains. The CUDA parity and bounded latency/profile gate is
satisfied, so the PR can leave draft with these limits recorded.
