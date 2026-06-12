# WP20-C Runtime Setup Consume Bridge

Status: `2026-05-21` accepted / focused pass.

Language:

- English canonical: `wp20_runtime_setup_consume_bridge_cluster_20260521.md`
- Chinese companion:
  [wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md](wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md)

Inputs:

- [WP20 main plan](public_capability_platform_composition_wp20_20260521.md)
- [WP20-B public typed platform spawn contract](wp20_public_typed_platform_spawn_contract_cluster_20260521.md)
- `src/core/engine/world_batch_runtime.*`
- `src/runtime/facade/runtime_facade.*`
- `src/models/core/default_unit_factory.h`

## Purpose

Consume validated typed platform spawn requests through the explicit
type-name projection resolved-plan bridge.

## Scope

In scope:

- runtime/facade setup execution that validates typed requests before spawn;
- materialization only through the preserved `source_type_name` projection path
  and admitted resolved plan;
- result evidence for admitted, materialized, and rejected typed requests;
- tests proving existing `spawn_requests` still behave unchanged.

Out of scope:

- direct arbitrary capability-bundle materialization;
- Python binding edits;
- scenario schema migration;
- new platform behavior.

## Task Items

| ID | Item | Acceptance |
|----|------|------------|
| `C1` | Validation before consume | Every typed request is validated before any spawn attempt. |
| `C2` | Type-name projection bridge | Materialization uses preserved `source_type_name` / resolved plan evidence, not arbitrary bundle semantics. |
| `C3` | Result evidence | Admitted/materialized/rejected typed results are returned according to B's ordering contract. |
| `C4` | Type-name projection preservation | Existing `spawn_units_batch` and `apply_world_setup_batch` tests remain valid. |

## Suggested Validation

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "world_setup or capability or spawn"
```

## Handoff

Return touched files, behavior summary, validation results, and any residuals
that must be exposed by D or closed by F.

Current implementation notes:

- `RuntimeFacade::apply_world_setup()` keeps `BatchWorldSetupResult.entity_ids`
  as the existing `spawn_requests` result channel and fills
  `typed_platform_spawn_results` separately in input order.
- Every typed request is passed through
  `validate_typed_platform_spawn_request()` before any spawn attempt.
- Runtime consume remains facade-local; `WorldBatchRuntime` does not gain a new
  typed public spawn API.
- The bridge only materializes through the preserved type-name projection path:
  admitted `resolved_spawn_plan` plus preserved `source_type_name`, then
  `spawn_unit(type_name)` semantics through the named projection materialization
  chain.
- Fail-closed runtime reasons used by this stream:
  `typed_platform_spawn_world_index_out_of_range` and
  `typed_platform_spawn_materialization_failed`.
- Validation failure, source-type mismatch, or rejected admitted-plan handoff
  stay fail-closed with the B contract reasons and append runtime diagnostics in
  `errors`.
- Successful typed materialization preserves helper-seeded evidence refs and
  appends runtime/facade bridge evidence afterward.

Public surface D must expose next:

- `BatchWorldSetupResult.typed_platform_spawn_results`
- every public field on `TypedPlatformSpawnResult`
- additive behavior where legacy callers can keep consuming `entity_ids` only
