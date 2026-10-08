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
and strict checkpoint loading. CUDA tests were skipped on this CPU-only host.
The CUDA latency/synchronization profile remains an explicit qualification gate
before claiming a GPU performance improvement. This PR is draft for that gate.
