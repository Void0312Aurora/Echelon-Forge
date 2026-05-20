# WP9-A DTO Promotion Batch 1

Status: `2026-05-20` complete / accepted WP9 parallel stream.

Language:

- English canonical: `wp9_dto_promotion_batch1_cluster_20260520.md`
- Chinese companion:
  [wp9_dto_promotion_batch1_cluster_20260520.zh.md](wp9_dto_promotion_batch1_cluster_20260520.zh.md)

Inputs:

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.md)
- [simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)
- [WP4 facade alignment acceptance review](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)
- [WP5 validation harness acceptance review](../../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

## 1. Purpose

WP9-A promotes the first DTO batch from accepted architecture vocabulary into
typed implementation surfaces. It closes the unstructured reward/termination
and observation-view gaps without changing ownership rules.

The stream covers:

- DTO-1 `RewardReport`
- DTO-2 `TerminationSpec`
- DTO-3 `ObservationBatchPacket` provenance metadata
- DTO-4 `ObservationViewSpec`

## 2. Required DTO Shape

| DTO | Required fields | Ownership rule |
|-----|-----------------|----------------|
| `RewardReport` | `fact_terms`, `shaping_terms`, `fact_snapshot_version`, `term_owner` | Simulation facts and experiment shaping must stay separable. Existing string JSON may remain only as compatibility text, not the authoritative typed shape. |
| `TerminationSpec` | `reason`, `reason_source`, `snapshot_version` | `reason_source` must distinguish at least `simulation`, `policy`, and `orchestration`. |
| `ObservationBatchPacket` metadata | `snapshot_version`, `barrier_id`, `source_time_s` | Metadata describes the sampled source, not a policy-owned belief. |
| `ObservationViewSpec` | `<major>.<minor>` `schema_version`, `required_fields`, `optional_fields`, checkpoint compatibility rule fields | Major mismatch must reject; minor-compatible optional-field drift may load only when required fields are satisfied. |

## 3. Implementation Route

Recommended route:

1. Add or update C++ contract headers under `src/runtime/contracts/` or
   `src/runtime/facade/` without importing engine owner types.
2. Add facade result fields only where the accepted runtime output already
   carries the corresponding information.
3. Expose Python bindings for the DTOs and fields.
4. Add focused binding and facade-shape tests.
5. Preserve compatibility fields such as `reward_breakdown_jsons` until a
   later migration explicitly removes them.

Preferred write scope:

- `src/runtime/contracts/*`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/*`
- `tests/runtime/facade/*`
- `tests/architecture/*`

Collision warning:

- `bindings_runtime.cpp` and `runtime_facade_types.h` are shared with WP9-B.
  If WP9-B is running concurrently, stop at a compile-ready contract patch and
  leave shared binding glue to WP9-E, unless the main thread assigns this
  worker as integration owner.

## 4. Work Items

| Stream | Required output | Budget |
|--------|-----------------|--------|
| `WP9-A1 RewardReport` | Typed reward report struct, Python binding fields, and tests that prove fact/shaping split exists. | High. |
| `WP9-A2 TerminationSpec` | Typed termination reason/source struct, Python binding fields, and tests for source labels. | High. |
| `WP9-A3 ObservationBatchPacket Metadata` | Provenance fields on packet output plus tests that metadata is visible from Python. | High. |
| `WP9-A4 ObservationViewSpec` | Versioned view spec struct/schema and compatibility tests for major/minor behavior. | Xhigh. |

## 5. Non-Goals

- Do not remove existing compatibility reward strings.
- Do not make policy or learning code the owner of simulation fact terms.
- Do not implement a full observation encoder in this stream.
- Do not change runtime stepping semantics.
- Do not claim a Python binding pass if the extension was not rebuilt or
  imported.

## 6. Acceptance Gates

WP9-A is ready for WP9-E when:

1. Every DTO-1 through DTO-4 has a typed C++ surface or an explicitly documented
   blocked implementation note with owner.
2. Python bindings expose the typed fields, or the exact binding build/import
   blocker is recorded.
3. Focused tests check field presence and default behavior.
4. Existing execution and observation compatibility paths still work.
5. The final notes identify any shared binding glue left to WP9-E.

## 7. Validation Commands

```bash
git diff --check
pytest tests/runtime/bindings tests/runtime/facade tests/architecture
rg -n "RewardReport|TerminationSpec|ObservationViewSpec|snapshot_version|barrier_id|source_time_s" src tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
