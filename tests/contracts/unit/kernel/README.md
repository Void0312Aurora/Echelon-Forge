# Simulation Kernel Contracts

This directory contains `unit_regression` contracts that step `SimulationKernel` directly with scripted pilot inputs.

## Current Failure Policy

The `sim_kernel` batch in `tests/runners/test_contract_batches.py` currently selects every `tests/contracts/unit/kernel/*.json` file by glob. Any selected failure exits non-zero, so the batch is operationally hard-fail today.

That runner behavior does not yet encode semantic tiers. Stable repeatability, sign, takeoff, ground-roll, and level-flight guardrails are gate candidates. Compact parameter scans and realism probes should be treated as supplemental or diagnostic until a metadata or manifest layer explicitly promotes them.

`pitch_hold_throttle_scan.json` is intentionally left unchanged here. Its current behavior remains whatever the runner reports; this README only documents that `sim_kernel` needs an explicit gate-vs-diagnostic split before scan failures can be interpreted as calibrated acceptance failures.
