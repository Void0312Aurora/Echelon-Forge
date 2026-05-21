# WP19-C GPU Helper Diagnostics Boundary

Status: `2026-05-21` pass / diagnostics non-promotion accepted.

Language:

- English canonical: `wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md`
- Chinese companion:
  [wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md](wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)

Inputs:

- [WP19 main plan](cuda_resident_state_alignment_wp19_20260521.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP18 facade contract hardening](../wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.md)

## Purpose

Keep CUDA helper availability and probe output useful while preventing them from
becoming accidental maintained capability evidence.

## Scope

In scope:

- architecture/runtime tests that prove helper/probe availability remains
  diagnostics or export-only until backend profile evidence promotes it;
- inventory of build flags and probe outputs that could be misread as support;
- guard recommendations for runtime capability projection and bindings.

Out of scope:

- resident-state sync/shard semantics, owned by WP19-D;
- device output contract design, owned by WP19-B;
- exact GPU promotion.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `C1` | Non-promotion tests | Existing or new tests prove GPU helper/probe availability does not flip maintained support flags. |
| `C2` | Diagnostics labels | Probe/helper outputs are classified as diagnostics/export-only unless promoted by a maintained profile. |
| `C3` | Runtime projection guard | Capability projection remains explainable from maintained profiles plus probeable deployment facts. |
| `C4` | Misuse inventory | Any risky helper/probe wording or API shape is routed to B/D/E. |

## First-Wave Guard Notes

- `probe_gpu_device()` facts such as CUDA build presence, runtime availability,
  device count, compute capability, memory totals, and device name are
  deployment diagnostics only. They cannot authorize exact GPU,
  resident-state, device-observation-view, shadow, or multi-fidelity support.
- Helper stats such as `last_visual_experiment_stats()`,
  `last_execution_observation_stats()`, `last_flight_shaping_stats()`, and
  `used_cuda` timing fields are experiment/probe evidence only. They are not
  maintained parity evidence and must not be projected as support flags.
- `EF_ENABLE_CUDA_EXPERIMENTS` and device-resident export handles may widen
  helper execution or export paths, but they must not be read by
  `RuntimeFacade.capabilities()` when projecting maintained support.
- The diagnostics-only backend profile
  `gpu_helpers.diagnostics_only` must remain `export-only`, keep host truth
  ownership, describe helper/probe state as non-committing diagnostics, and
  explicitly keep exact GPU, resident-state, shadow, and device observation
  support false.

## Misuse Inventory

- Build success or `EF_ENABLE_CUDA_EXPERIMENTS` enablement could be misread as
  exact GPU readiness. WP19-C treats this as a non-promotion signal only; any
  future promotion proof belongs to WP19-B/D/E plus a maintained profile gate.
- Device-view exports from helper bindings could be misread as maintained
  resident-state or device-observation support. WP19-C keeps them in
  diagnostics/export-only tests and routes consumer contract questions to
  WP19-B.
- Probe summaries and helper timings could be misread as parity evidence or
  multi-fidelity readiness. WP19-C keeps them as diagnostics-only facts and
  routes parity/sync obligations to WP19-D and any future runtime slice to
  WP19-E.

## Preflight Outcome

- Preferred implementation shape for this stream is tests plus guard notes
  only.
- No CUDA helper implementation changes are required for this first-wave
  boundary hardening.
- Resident-state sync/shard semantics remain untouched and explicitly deferred
  to WP19-D.

## Suggested Validation

```bash
git diff --check
python -m pytest -q tests/test_gpu_runtime_bindings.py
python -m pytest -q tests/architecture/test_runtime_facade_layering.py
```

## Handoff

Return guard/test changes, helper/probe risk list, residuals for B/D/E, and
whether any code path can currently mis-project support.

## Closure Outcome

WP19-C is accepted for WP19 as a diagnostics non-promotion boundary. CUDA build
presence, probe facts, helper timing, device pointers, and
`EF_ENABLE_CUDA_EXPERIMENTS` remain deployment diagnostics or export-only
evidence and cannot promote exact GPU, resident-state, shadow, or device
observation support.
