# WP21-B Snapshot Restore And Worldline Boundary

Status: `2026-05-21` planned; waits for WP21-A facts.

Language:

- English canonical: `wp21_snapshot_restore_worldline_boundary_cluster_20260521.md`
- Chinese companion:
  [wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md](wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md)

Inputs:

- [WP21 main plan](full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP17 counterfactual runtime slice](../wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)
- [WP19 resident-state boundary rules](../wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md)

## Purpose

Broaden the accepted selected-entity snapshot/branch path into the minimal
bounded snapshot/restore boundary needed by the final counterfactual runtime.

## Scope

In scope:

- snapshot and restore of declared host-owned state needed by the first full
  experiment runtime slice;
- worldline identity, seed, barrier, provider/fidelity, and evidence refs;
- facade-owned restore authority and fail-closed rejection reasons;
- focused C++/facade/binding tests if public DTOs change.

Out of scope:

- exact GPU or resident-state promotion;
- arbitrary live-world cloning without explicit boundary evidence;
- experiment orchestration or scenario generation.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `B1` | Snapshot boundary DTO/runtime | Declared host-owned state is captured with worldline id, barrier id, deterministic seed, provider/fidelity, and evidence refs. |
| `B2` | Restore boundary runtime | Restore applies only through facade authority and rejects unsupported state, raw mutation, invalid worldline ids, and backend/resident-state claims. |
| `B3` | Worldline registry seed | Parent/branch worldline ids are tracked enough for C to run independent rollouts. |
| `B4` | Public surface proof | Facade/binding tests prove the boundary is reachable and fail-closed if public DTOs are exposed. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or worldline or restore or snapshot"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "counterfactual or worldline"
```

## Handoff

Return snapshot schema, restore semantics, rejected unsupported claims, touched
files, commands run, and exact assumptions C must consume.
