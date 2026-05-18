# Naval Standards Placeholder

This directory is reserved for standards documentation related to the upcoming `naval` module.

Its current purpose is limited to:

- Providing a clear landing point for the `common + air + naval` split.
- Providing a freeze entry point for the minimal naval task structure, see [minimal_task_structure.md](minimal_task_structure.md).
- Providing sources and modeling boundaries for the first batch of real warship units, see [ship_unit_references.md](ship_unit_references.md).

## 1. Directory Responsibilities

Documents placed here in the future should only describe naval-specific semantics, for example:

- `warfare_role_code`
- `officer_in_tactical_command`
- Tight-loop runtime interpretation of `task force / task group / task unit`
- Fleet cooperation semantics such as screen / support / station
- Naval route / recovery / replenishment / station-keeping rules

## 2. Content That Should Not Be Placed Here

- `command_relationship`
- `authority_scope`
- `task_family`
- `service_profile`
- `tactical_unit_type`
- `coordination_mode`
- Other `common` fields that still hold across military branches

These should continue to be governed by `docs/standards/joint/` and `docs/standards/services/`.

## 3. Relationship with air

`naval` is not a simple renaming of existing air documentation.

Subsequent naval documentation should avoid default use of:

- `lead / wingman`
- `runway`
- `CAP`
- air-style interpretation of `MissionCommand.command_code`

If an object is only valid in an air combat sortie-level scenario, it should remain in `docs/standards/air/`.

## 4. Current Minimal Naval Placeholder Stance

- `Red_Surface_Combatant_Minimal` belongs to a `community-derived approximation`, used only to replace the previous incorrect placeholder that treated a supply ship as an enemy vessel. It does not represent precise public parameters of any specific enemy ship class.
- `ReportTrack` / task-group-level sharing is an engineering approximation converged from current data link realities, used to avoid stepwise flooding broadcasts; it is not equivalent to the full `Link 16 / CEC` semantics.
