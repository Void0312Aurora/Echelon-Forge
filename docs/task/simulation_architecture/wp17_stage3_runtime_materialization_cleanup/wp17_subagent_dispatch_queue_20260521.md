# WP17 Subagent Dispatch Queue

Status: `2026-05-21` implementation waves returned; selected-slice validation
passed.

Use this queue when launching subagents. The main thread owns integration and
final acceptance.

Preflight recovery:

- [WP17 first-wave preflight recovery](wp17_preflight_recovery_20260521.md)

## First Wave

| Stream | Agent type | Model / reasoning | Task | Write scope |
|--------|------------|-------------------|------|-------------|
| `WP17-A` | explorer or lightweight worker | `gpt-5.4-mini`, xhigh | Verify the code-fact ledger and residual boundaries against current source/tests. | Docs/fixtures only; no runtime code. |
| `WP17-B` | worker | `gpt-5.4`, high | Plan and, when authorized, implement facade-shaped batch/training read migration and compatibility guards. | `python/rl/runtime/world_batch*`, selected `tests/world_batch`, selected architecture guards. |
| `WP17-C` | worker | `gpt-5.4`, xhigh | Preflight the §8 multi-rate runnable example and name exact scheduler seams/tests. | Scheduler/window-loop files and focused cadence tests only. |
| `WP17-D` | worker | `gpt-5.4`, high | Preflight fidelity request/provider runtime slice and name binding/test surfaces. | Runtime facade capability/provider files and fidelity tests only. |
| `WP17-E` | worker | `gpt-5.4`, high | Preflight capability spawn promotion and compatibility risks. | Default unit factory/setup/spawn tests only. |

## Historical First-Wave Return State

| Stream | Dispatch status | Preflight result | Planning consequence |
|--------|-----------------|------------------|----------------------|
| `WP17-A` | dispatched / returned | `pass` | Six current-code facts in the WP17 main plan are accurate; stale Stage 3 wording about empty capabilities must not drive implementation. |
| `WP17-B` | dispatched / returned | `pass` | Maintained business code already routes through adapter methods; next implementation should migrate remaining test reads and tighten compatibility guards. |
| `WP17-C` | dispatched / returned | historical preflight gap | At preflight time, the architecture §8 multi-rate example still needed selected-slice cadence planning, hold/expiry evidence, and runtime window traces. |
| `WP17-D` | dispatched / returned | historical preflight gap | At preflight time, contract-level fidelity admission existed but facade-owned admission/provider-selection runtime behavior had not yet been added. |
| `WP17-E` | dispatched / returned | historical preflight gap | At preflight time, capability contracts/bindings/factory internal resolution existed but spawn materialization had not yet consumed resolved plans. |

## Implementation Return State

| Stream | Implementation status | Evidence |
|--------|-----------------------|----------|
| `WP17-B` | implemented / focused pass | Maintained adapter/env methods expose facade-shaped execution-episode ready/state reads; architecture guards keep direct `batch_runtime` reads compatibility-only. |
| `WP17-C` | implemented / focused pass | Runtime window selected-slice cadence emits `cadence_config`, `cadence_trace`, hold/expiry evidence, and the `selected_slice_cadence_trace_runtime_window_wp17c` reason. |
| `WP17-D` | implemented / focused pass | `RuntimeFacade::admit_fidelity_request()` admits reference CPU exact evaluation and rejects resident/exact-GPU/shadow requests. |
| `WP17-E` | implemented / focused pass | `DefaultUnitFactory::spawn()` consumes resolved platform spawn plans internally while preserving `spawn_unit(type_name)` compatibility. |
| `WP17-F` | narrowed selected-slice implemented / focused pass | `RuntimeFacade::run_counterfactual_branch()` builds parent/branch worlds from explicit setup, rejects raw mutation, and reports selected-entity causal deltas. |

## Held Wave

| Stream | Release condition |
|--------|-------------------|
| Broad counterfactual/worldline rollout | Release only after arbitrary live-world clone, snapshot/restore support, and experiment orchestration have separate runtime evidence. |

## Required Worker Return Packet

```md
Stream:
Status: pass | fail | blocked
Touched files:
Commands run:
Evidence:
Residuals:
Integration notes:
Closure impact:
```
