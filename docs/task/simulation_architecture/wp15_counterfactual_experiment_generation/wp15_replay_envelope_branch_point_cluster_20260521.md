# WP15-A Replay Envelope And Branch Point Contract

Status: `2026-05-21` mergeable / first slice complete.

Language:

- English canonical: `wp15_replay_envelope_branch_point_cluster_20260521.md`
- Chinese companion:
  [wp15_replay_envelope_branch_point_cluster_20260521.zh.md](wp15_replay_envelope_branch_point_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- [WP2.5 scheduler semantics freeze](../wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)
- Current `src/runtime/contracts/*`
- Current `python/world_model/replay.py`

## 1. Purpose

`WP15-A` creates the deterministic replay envelope and branch point vocabulary
that every later counterfactual stream consumes. The contract must name the
baseline seed, snapshot/barrier/event-order evidence, facade provenance, and
branch point identity without claiming restore execution.

## 2. Scope

In scope:

- typed `ReplayEnvelope` and `BranchPoint` or equivalent code-owned contracts;
- seed, episode, snapshot version, barrier id, event-order, source-time, and
  facade provenance references;
- validation helpers that reject missing ancestry;
- focused architecture tests proving deterministic shape and fail-closed
  behavior.

Out of scope:

- full snapshot/restore implementation;
- worldline parent/child metadata owned by `WP15-B`;
- counterfactual request admission owned by `WP15-C`;
- scenario/adversary generation owned by `WP15-D`.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/stage_node_manifest_registry.h`
- `src/runtime/facade/runtime_window_coordinator.h`
- `src/runtime/contracts/runtime_dto_contracts.h`
- `python/world_model/replay.py`
- `tests/architecture/test_wp10_*.py`

Preferred approach:

- add a new counterfactual/replay-focused contract surface rather than
  overloading backend or platform capability contracts;
- keep required fields string-testable and deterministic;
- include explicit `snapshot_restore_supported = false` or equivalent support
  boundary until a restore proof exists;
- use stable rejection reason strings for missing envelope id, seed, snapshot,
  barrier, event-order, and provenance refs.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Deterministic envelope | Replay envelope names seed, episode/run, snapshot, barrier, event-order, and provenance evidence. |
| Branch point identity | Branch point ids are stable and tied to a replay envelope plus snapshot/barrier boundary. |
| Restore boundary | The first slice may name restore prerequisites but must not claim restore support. |
| Fail-closed validation | Missing id, seed, snapshot, barrier, event-order, or provenance refs reject the fixture. |

## 5. Acceptance Tests

Minimum tests:

- architecture test builds a valid replay envelope and branch point fixture;
- validation rejects missing envelope id, deterministic seed, snapshot version,
  barrier id, event-order ref, and facade provenance ref;
- test proves restore support is not implied by envelope existence;
- test proves deterministic ordering of evidence refs.

Suggested commands:

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp15_replay_envelope_contracts.py
```

## 6. Handoff Contract

Return:

- contract files touched;
- replay envelope and branch point field names;
- validation helper names and rejection reasons;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP15-B`, `WP15-C`, or `WP15-E`.
