# WP20-B Public Typed Platform Spawn Contract

Status: `2026-05-21` implemented / focused pass.

Language:

- English canonical: `wp20_public_typed_platform_spawn_contract_cluster_20260521.md`
- Chinese companion:
  [wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md](wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [WP20-A fact ledger](wp20_public_capability_fact_ledger_cluster_20260521.md)
- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`

## Purpose

Define the public admission/result contract needed before typed platform spawn
requests can be consumed by setup execution.

## Scope

In scope:

- additive result/admission DTO fields for request id, entity id, validity,
  fail-closed state, rejection reason, source type-name, resolved plan id,
  capability bundle id, and evidence refs;
- result ordering rules across legacy `spawn_requests` and typed platform
  requests;
- validation rules that keep typed setup optional and fail closed;
- focused architecture/DTO tests.

Out of scope:

- runtime materialization;
- Python bindings, unless needed only for compile surface discovery;
- scenario schema migration;
- public `spawn_platform` convenience API.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `B1` | Result DTO shape | A public result/admission DTO exists and carries request/entity/evidence fields. |
| `B2` | Ordering contract | The ordering of returned ids/results is documented and test-backed. |
| `B3` | Fail-closed reasons | Missing ids, invalid bundles, invalid plans, missing evidence, and compatibility loss all reject with stable reasons. |
| `B4` | Optionality | Legacy `WorldSpawnRequest` and `spawn_unit(type_name)` remain maintained compatibility surfaces. |

## Candidate Shape

Implemented additive shape:

- keep `BatchWorldSetupResult.entity_ids` compatible;
- add `BatchWorldSetupResult.typed_platform_spawn_results`;
- define `TypedPlatformSpawnAdmission` for validation/admission handoff before
  materialization;
- define `TypedPlatformSpawnResult` for public result propagation after
  admission/materialization;
- keep all new fields additive and public-contract only; runtime behavior is
  unchanged in this stream.

Implemented field set:

- `TypedPlatformSpawnAdmission`:
  `request_index`, `world_index`, `admitted`, `fail_closed`, `request_id`,
  `source_type_name`, `plan_id`, `capability_bundle_id`, `rejection_reason`,
  `errors`, `evidence_refs`.
- `TypedPlatformSpawnResult`:
  `request_index`, `world_index`, `entity_id`, `admitted`, `materialized`,
  `fail_closed`, `request_id`, `source_type_name`, `plan_id`,
  `capability_bundle_id`, `rejection_reason`, `errors`, `evidence_refs`.

Helper shape exposed to C:

- `collect_typed_platform_spawn_evidence_refs(const TypedPlatformSpawnRequest&)`
  deduplicates facade, bundle-template, bundle, plan-template, resolution,
  materialization, and plan evidence in first-seen order.
- `make_typed_platform_spawn_admission(...)` seeds a stable admission record
  from a request.
- `make_typed_platform_spawn_result(...)` converts an admission into the public
  result DTO without forcing materialization.

## Ordering Rule

The public ordering contract for `typed_platform_spawn_results` is:

1. one result entry per input
   `BatchWorldSetupRequest.typed_platform_spawn_requests[i]`;
2. `typed_platform_spawn_results[i].request_index == i` for the maintained
   request vector order;
3. typed request results do not reorder or reinterpret legacy
   `BatchWorldSetupResult.entity_ids`;
4. `entity_ids` remains the legacy result channel for materialized legacy
   `spawn_requests`, while typed request outcomes are consumed from
   `typed_platform_spawn_results`;
5. a typed request that is validated/admitted but not yet materialized still
   returns an entry with `admitted=true`, `materialized=false`, `entity_id=0`.

This rule gives `WP20-C` a stable way to fill results without creating an
implicit zip contract across legacy and typed spawn collections.

## Fail-Closed Reasons

Stable typed spawn rejection reasons now include:

- `typed_platform_spawn_request_id_required`
- `typed_platform_spawn_source_type_name_required`
- `typed_platform_spawn_requires_capability_bundle`
- `typed_platform_spawn_capability_bundle_invalid`
- `typed_platform_spawn_requires_resolved_spawn_plan`
- `typed_platform_spawn_resolved_plan_invalid`
- `typed_platform_spawn_requires_typed_platform_request_kind`
- `typed_platform_spawn_requires_type_name_compatibility_path`
- `typed_platform_spawn_evidence_required`
- `typed_platform_spawn_world_index_out_of_range`
- `typed_platform_spawn_materialization_failed`

`WP20-B` only declares the contract-level reasons. `WP20-C` must use the new
world-index/materialization reasons if setup consumption rejects after request
validation.

## Exact Interface For C/D

`WP20-C` must consume:

- `TypedPlatformSpawnAdmission`
- `TypedPlatformSpawnResult`
- `make_typed_platform_spawn_admission(std::uint64_t request_index, const TypedPlatformSpawnRequest& request)`
- `make_typed_platform_spawn_result(const TypedPlatformSpawnAdmission& admission)`
- `collect_typed_platform_spawn_evidence_refs(const TypedPlatformSpawnRequest& request)`
- `BatchWorldSetupResult.typed_platform_spawn_results`

`WP20-C` fill rules:

- preserve `request_index`, `world_index`, `request_id`, `source_type_name`,
  `plan_id`, `capability_bundle_id`;
- set `admitted` only after validation/bridge admission;
- set `materialized` only after the compatibility-preserving spawn succeeds;
- on rejection, set `fail_closed=true`, stable `rejection_reason`, and append
  any bridge/runtime diagnostic text to `errors` without replacing the stable
  reason;
- keep `evidence_refs` in the helper-produced order, appending any new bridge
  evidence after the pre-seeded refs.

`WP20-D` must expose:

- `BatchWorldSetupResult.typed_platform_spawn_results`
- all public fields on `TypedPlatformSpawnResult`
- default additive behavior where legacy callers that ignore the new field
  remain compatible.

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp20_public_typed_platform_spawn_contract.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp14_additive_platform_spawn_dto.py
```

## Handoff

Return touched files, DTO/result shape, ordering rule, tests run, blockers, and
the exact contract C/D must consume.
