# Ground Mission Domain

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/README.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

The Ground owner defines land-domain specialization semantics without turning
Army service doctrine into a private runtime stack. It owns Ground-specific
platform identity and static task/status vocabulary. Joint relationships,
Army service-profile interpretation, and cross-domain runtime architecture
remain with their respective owners.

## Current Authority

- [Ground Specialization Baseline](standards/specialization_baseline.md):
  canonical Ground identity, owner boundaries, accepted implementation surface,
  and held runtime claims.
- [Ground Minimal Task Structure](standards/minimal_task_structure.md):
  the maintained `TASK_MOVE`, `TASK_OCCUPY`, and `TASK_SUPPORT` static
  task/status contract.

## Current Implemented Surface

- `army`, `ground`, `land`, and `ServiceProfile.Army` route through the
  maintained `ground` tasking profile.
- `Ground_Platoon_MVP` is a runtime-loadable native `UnitType::Ground` content
  definition for static schema and scenario-loader evidence.
- Ground-owned component slices carry static command/task/status fields through
  `TaskOrder`, `LeaderIntent`, `PilotReport`, and `MissionCommand` compatibility
  shells.
- The maintained tasking cadence baseline is `1 Hz`.
- There is no `src/systems/domains/ground/` runtime-system owner. Route
  movement, terrain interaction, sensing, fires, effects, damage, suppression,
  logistics, and Ground observation export remain held.

Directory placement does not broaden those claims. The current evidence proves
native identity and a static task/status chain, not a complete land-combat
runtime.

## Current Work Route

- [Ground task area](../../task/ground/README.md): current implementation status,
  remaining held boundaries, and execution planning.

Task documents may report maturity and evidence, but they do not redefine the
standards above.

## Related Owners

- [Joint mission domain](../joint/README.md): shared authority and common-core
  command relationships.
- [US Army service profile](../joint/service_profiles/standards/army_profile.md):
  Army organization and service-level interpretation.
- [Runtime workflow and contract baseline](../../architecture/standards/runtime_workflow_and_contract_baseline.md):
  shared stage and runtime boundaries, pending its separate owner migration.
