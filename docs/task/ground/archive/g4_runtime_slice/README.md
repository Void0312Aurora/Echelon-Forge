# G4 Runtime Slice

Status: `2026-05-22` implemented and validated for one bounded tasking-only
lifecycle-proof slice selected by G3.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G3 execution surface design](../g3_execution_surface_design/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Implement one selected, maintained ground behavior slice through the shared
simulation lifecycle.

## Output

- [G4 selected runtime slice cluster](g4_selected_runtime_slice_cluster_20260521.md)
- [G4 subagent dispatch packets](g4_subagent_dispatch_packets_20260522.md)

## Scope

In scope:

- one G3-selected runtime behavior
- focused tests proving shared lifecycle participation
- compatibility guards proving no private ground runtime path
- validation rollup and residual map

Out of scope:

- broad ground movement model
- direct-fire or indirect-fire runtime
- full terrain, logistics, or damage model
- public schema expansion beyond the selected slice

## Gate

G4 is mergeable when one ground behavior is exercised through maintained shared
entry points and tests prove air/naval compatibility is preserved.

Released slice:

- `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`

Still held:

- formal `CommandPacket`
- formal `ObservationPacket`
- formal `TrackPacket`
- formal `P3`
- formal `P10`
- movement, sensing, terrain, fires, effects, DTO/binding expansion, and broad
  `MissionCommand` growth

Validation result:

- Runtime batch command-chain sync now imports
  `python.rl.tasking.bridge.build_kernel_mission_command`.
- Focused G4 bridge test passed.
- Ground/common-core/naval/leader compatibility tests passed.
- Ground unit contracts passed through the contract runner.
