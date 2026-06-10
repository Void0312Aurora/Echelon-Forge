# WP15-B Worldline Branch Metadata Gate

Status: `2026-05-21` mergeable / first slice complete.

Language:

- English canonical: `wp15_worldline_branch_metadata_gate_cluster_20260521.md`
- Chinese companion:
  [wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md](wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- [WP15-A replay envelope and branch point](wp15_replay_envelope_branch_point_cluster_20260521.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)
- Current scenario compiler branch isolation tests in `tests/scenario/test_scenario_compiler.py`

## 1. Purpose

`WP15-B` defines how a potential branchable worldline is named, traced, and
rejected when prerequisites are missing. It should let later code reason about
parent/child worldline metadata without pretending that snapshot restore or
counterfactual rollout execution is already maintained.

## 2. Scope

In scope:

- baseline, parent, and child worldline identifiers;
- branch point reference and replay envelope reference;
- branch reason, mutation/intervention intent, source, and evidence refs;
- explicit support state for metadata-only, admitted, rejected, and unsupported
  restore cases;
- tests that reject raw state mutation or missing ancestry.

Out of scope:

- executing a restored branch;
- admitting counterfactual requests owned by `WP15-C`;
- scenario/adversary generation owned by `WP15-D`;
- capability or experiment scoring owned by `WP15-E`.

## 3. Candidate Implementation Seams

Inspect before editing:

- output from `WP15-A`;
- `tests/scenario/test_scenario_compiler.py` branch isolation fixtures;
- `python/scenario/compiler/clone.py`;
- `src/runtime/contracts/runtime_dto_contracts.h`;
- `src/runtime/contracts/world_batch_contracts.h`.

Preferred approach:

- add worldline metadata near the replay/counterfactual contract surface after
  A has named shared vocabulary;
- keep scenario compiler branch isolation as supporting evidence, not as a
  runtime worldline guarantee;
- include stable rejection reasons for missing parent id, child id, branch
  point, replay envelope, mutation intent, and evidence refs.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Parent/child identity | Branch metadata names baseline or parent worldline and child worldline without collision. |
| Ancestry | Every branch references a replay envelope and branch point. |
| Mutation intent | Intervention or mutation intent is explicit and source-attributed. |
| Unsupported restore | Metadata can be valid while executable restore remains unsupported and visible. |

## 5. Acceptance Tests

Minimum tests:

- valid branch metadata fixture references A's replay envelope and branch point;
- validation rejects missing parent/child ids, branch point, envelope, mutation
  intent, or evidence refs;
- validation rejects raw state mutation claims outside request contracts;
- test confirms metadata-only branches do not imply snapshot/restore support.

Suggested commands:

```bash
git diff --check
python -m pytest -q tests/architecture/causal_runtime/test_worldline_branch_metadata.py
python -m pytest -q tests/scenario/test_scenario_compiler.py -k "branch or runtime"
```

## 6. Handoff Contract

Return:

- metadata files touched;
- worldline status and rejection vocabulary;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP15-C` or `WP15-E`.
