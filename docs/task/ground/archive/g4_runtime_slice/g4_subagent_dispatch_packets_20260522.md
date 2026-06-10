# G4 Subagent Dispatch Packets

Status: `2026-05-22` dispatch packet for the released G4 tasking-only
lifecycle-proof slice.

Language:

- English canonical: `g4_subagent_dispatch_packets_20260522.md`
- Chinese companion: not required for this high-churn worker packet.

Inputs:

- [G4 README](README.md)
- [G4 selected runtime slice cluster](g4_selected_runtime_slice_cluster_20260521.md)
- [G3 execution surface preflight cluster](../g3_execution_surface_design/g3_execution_surface_preflight_cluster_20260521.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Dispatch one worker packet that validates the released G4 slice without
expanding the runtime surface. The packet is intentionally small: it verifies
the normalized tasking lifecycle shell, the no-private-path proof, and the
residual handoff.

## Worker Packet

### `G4-A` Lifecycle shell

Task:

- confirm the normalized ground lifecycle shell is `TaskOrder -> LeaderIntent ->
  PilotReport`
- keep the slice limited to a status shell

Acceptance:

- no command-delivery, movement, sensing, terrain, fires, or effects semantics
  are introduced
- the released slice still routes through shared maintained entry points

### `G4-B` Validation commands

Task:

- run the focused validation commands that prove the slice and preserve
  compatibility
- capture the exact command list in the handoff

Acceptance:

- validation commands are explicit, repo-root runnable, and limited to the
  released slice

### `G4-C` No-private-path proof

Task:

- show the maintained `tasking_profile` bridge is used
- rule out private imports, ground-only loops, and air-only shortcuts

Acceptance:

- the proof does not rely on route refs, recovery base/runway fields,
  landing/takeoff semantics, world-truth observation surfaces, or deferred
  terrain/LOS/radio runtime

### `G4-D` Residual map

Task:

- record what remains held after the released slice is validated

Acceptance:

- residuals explicitly include `CommandPacket`, `ObservationPacket`,
  `TrackPacket`, `P3`, `P10`, movement, sensing, terrain, fires, and broad
  `MissionCommand` growth

## Validation Commands

```bash
git diff --check
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/leader/test_tasking_profile_contracts.py
python -m pytest -q tests/runtime/mission/test_leader_tasking_runtime.py
python -m pytest -q tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py
python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
```

## Handoff

Return:

- touched files
- commands run
- compatibility results
- no-private-path proof
- residual map
