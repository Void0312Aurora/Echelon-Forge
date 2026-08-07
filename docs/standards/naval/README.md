# Naval Standards

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Status: `2026-06-10` specialization entrypoint for maintained naval semantics.

This directory contains the authoritative standards for the dedicated `naval` specialization.

It is the legacy standard landing point for the current naval task plan, not a
placeholder. The goal is to separate Joint common core, the owner-local Navy
service profile, and Naval specialization cleanly enough that runtime and
planning work can continue without air-first assumptions leaking into maritime
semantics.

## Maintained Documents

Read these files together:

1. [Naval Minimal Task Structure](minimal_task_structure.md)
2. [Ship Unit References](ship_unit_references.md)
3. [Naval Observation Contract](obs.md)

## 1. Layer Model

### `common`

The shared layer keeps the cross-service contract stable.

It owns fields such as:

- `service_profile`
- `task_family`
- `task_group_id`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `supported_node_id / supporting_node_id`
- `recovery_site_id`
- `tactical_unit_type`

These are service-neutral shapes. They are not naval execution semantics.

### Navy service profile

The [Navy service profile](../../domains/joint/service_profiles/standards/navy_profile.md)
explains how the shared contract should be read for naval warfare.

It owns the interpretation of:

- `task_group` and `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- shared anchors that the Navy profile needs for task packaging and authority assignment

### `naval`

The `naval` specialization owns the tight-loop maritime semantics:

- `screen`
- `support`
- `station`
- `recover`
- ship and formation control semantics
- maritime recovery and station-keeping behavior

## 2. Minimal Semantic Contract

The minimal naval semantic set now treated as first-class is:

- `task_group`
- `task_unit`
- `warfare_role_code`
- `officer_in_tactical_command`
- `screen`
- `support`
- `station`
- `recover`

These are the smallest terms needed to make the current task plan meaningful without overfitting to air sortie language.

## 3. What Belongs Here

Documents in this directory should describe naval-specific semantics, such as:

- task-group and task-unit ownership
- warfare role allocation
- station holding and recovery behavior
- screen/support relations in a naval formation
- command authority in maritime tasking
- naval execution and reporting specialization

## 4. What Does Not Belong Here

The following should remain in Joint common core or the Navy service profile:

- `command_relationship`
- `authority_scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `coordination_mode`
- other cross-service contract fields

This directory should not re-litigate the shared schema. It should specialize it.

## 5. Relationship with Air

`naval` is not a rename of air documentation.

Naval documentation should avoid default air concepts such as:

- `lead / wingman`
- `runway`
- `CAP`
- air-style reading of `MissionCommand.command_code`

If a concept is only valid for air sortie-level runtime, it should stay in `docs/domains/air/`.

## 6. Current Minimal Naval Meaning

The current minimal naval semantics now expected by the runtime bridge are:

- `task_group / task_unit` as the tactical organization boundary
- `officer_in_tactical_command` as the authority owner
- `warfare_role_code` as the role label
- `screen / support / station / recover` as the minimal operational vocabulary

These terms are enough to support the present naval task plan without pretending the full fleet doctrine is already modeled.
