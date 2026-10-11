# Structural Breakup Topology Contract

Language:
- English canonical: `structural_breakup_topology_contract.md`
- Chinese companion: [structural_breakup_topology_contract.zh.md](structural_breakup_topology_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/structural_breakup_topology_contract.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

Structural breakup selects an explicit topology profile carried by
`HitboxConfig` and copied into `ComponentDamageState`. Component names alone do
not admit the specialized path.

## Profiles and admission

- `default_shared_spar_v1` is the default and uses the shared spar, engine-core,
  control-surface, fuel-cell, tail, and fuselage contributors.
- `tg_p7_split_surface_v1` admits the split-surface mapping only when all eight
  split receivers are present: three engine segments, four wing-spar segments,
  and the wing-spar carry-through segment.
- A declared TG-P7 profile with an incomplete receiver set is explicitly
  classified as `TgP7IncompleteFallback` and uses the default shared-spar path.
- Unknown profile identifiers are rejected by the unit-definition loader. A
  directly constructed runtime state with an unknown identifier fails closed to
  the default path.

The TG-P7 thresholds and outcomes remain unchanged after admission. The
profile controls only which already-maintained topology mapping is eligible.

## Breakup interpretation

- `active_structural_groups` counts physical detached groups.
- `active_break_modes` is a family mask derived from those groups.
- `detached_part_count` counts active physical groups, not mode families.
- `breakup_state` is derived from the number of unique mode families:
  one family gives `PartialDetachment`, two gives `PartialBreakup`, and three
  or more gives `FullBreakup` plus `MultiAxis`.
- Mobility and loss consequences consume the resulting mode mask separately;
  they are not inferred from the detached-part count.

The native structural-failure tests cover the shared-spar synthetic profile,
complete TG-P7 admission, incomplete-profile fallback, family counting, and
the existing TG-P7 outcome parity.
