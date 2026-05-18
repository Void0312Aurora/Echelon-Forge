# Forward Docs vs Code Review

## README.md

### Mismatches
- **Claim**: Lists `release_alpha_checklist.md` as a forward document.
  **Reality**: File does not exist anywhere in the repository.
  **Severity**: P1

---

## c2_communication.md

### Verified
- `CommandLink`: verified at `src/components/command/command_link.h`
- `MovementCommand`: verified at `src/components/command/legacy_command.h`
- `ActionCommand`: verified at `src/components/command/legacy_command.h`

### Mismatches
- **Claim**: "Data structures: `src/components/action.h`"
  **Reality**: File does not exist. Actual location: `src/components/command/legacy_command.h` (for `MovementCommand`, `ActionCommand`) and `src/components/command/command_link.h` (for `CommandLink`).
  **Severity**: P1

- **Claim**: "Link system: `src/systems/command_link_system.h`"
  **Reality**: File does not exist. Actual: `src/systems/core/operation_system.h` (functions `register_action_mapping_system()` and `register_command_lag_system()`).
  **Severity**: P1

- **Claim**: "Delivery logic: `src/core/simulation_kernel.cpp`"
  **Reality**: File does not exist. Actual: `src/core/engine/simulation_kernel.cpp`.
  **Severity**: P1

- **Claim**: "`PendingCommand`: queues commands and delivers them at the scheduled time."
  **Reality**: No `PendingCommand` struct or class found. Closest: `CommandLag` / `LaggedCommand` in `src/components/command/legacy_command.h` which applies lag (tau-based), not scheduled delivery.
  **Severity**: P1

---

## engagement_termination.md

### Verified
- Termination runtime: `src/core/mission/runtime/termination_runtime.h` (exists but at different path than claimed)

### Mismatches
- **Claim**: "`disengage_range_m` + `disengage_hold_s`" — distance threshold disengagement.
  **Reality**: Neither field exists anywhere in the codebase.
  **Severity**: P1

- **Claim**: "`min_specific_energy_j_kg` + `energy_hold_s`" — low energy disengagement.
  **Reality**: Neither field exists. `specific_energy` only appears in test assertions (`tests/runtime/test_flight_dynamics_realism_guards.py`), not in termination logic.
  **Severity**: P1

- **Claim**: "`ammo_depletion_ends` plus in-flight missile checks"
  **Reality**: `ammo_depletion_ends` not found. No ammunition depletion termination logic found.
  **Severity**: P1

- **Claim**: "Main implementation: `src/core/mission/termination_runtime.*`"
  **Reality**: Actual path: `src/core/mission/runtime/termination_runtime.*` (missing `runtime/` subdirectory).
  **Severity**: P2

- **Claim**: "`gym_envs/scenario_loader.py`"
  **Reality**: Not a file — is a directory `gym_envs/scenario_loader/` containing multiple module files.
  **Severity**: P2

---

## improvement_backlog.md

### Verified
- `train.py`, `train.py` uses `python/training/`, `world_model_train.py`, `pyproject.toml`, `python/training/` — all verified.

No mismatches found.

---

## operation_layer.md

### Verified
- `ActionCommand`, `ActionSpaceConfig`, `CommandLag`, `LaggedCommand` — verified in `src/components/command/legacy_command.h`
- `ActionMapping` system, `CommandLag` system — verified in `src/systems/core/operation_system.h`

No mismatches found.

---

## physics_engine_roadmap.md

### Verified
- `src/models/air/default_control_model.cpp`, `src/systems/physics/leapfrog_system.h`, `src/systems/physics/aerodynamics_system.h`, `src/core/engine/simulation_kernel.cpp` — all verified.

### Mismatches
- **Claim**: Phase 1: `components/physics/forces.h` labeled `[NEW]`
  **Reality**: File already exists at `src/components/physics/forces.h` with full `ForceAccumulator` component implementation used by `LeapfrogIntegration`, `RotationalIntegrate`, `ClearForces`, and instrument system.
  **Severity**: P3 (misleading status label on already-implemented component)

---

## rl_selfplay.md

### Verified
- PyTorch MLP policy: verified at `python/rl/policy_algo/policies.py`

### Mismatches
- **Claim**: "The policy pool is implemented: `examples/training/train_self_play.py`"
  **Reality**: Directory `examples/training/` does not exist. No `train_self_play.py` found anywhere.
  **Severity**: P1

- **Claim**: "Configuration from `examples/training/selfplay_config.json`"
  **Reality**: File does not exist. No `selfplay_config.json` found anywhere.
  **Severity**: P1

---

## sensor_situation.md

### Verified
- All sensor parameters (`scan_period`, `last_scan_time`, `detection_prob`, `range_power`, `bearing_noise_std`, `range_noise_std`, `track_memory_s`, `aspect_influence`) — verified in `src/components/systems/sensor.h`
- `ContactList` — verified in `src/components/systems/sensor.h`
- Track memory logic — verified in `src/systems/systems/sensor_system.h`

No mismatches found.

---

## weapons_engagement.md

### Verified
- Seeker FOV + lock range, PN guidance (`nav_gain`), guidance logic — all verified.

No mismatches found (this is a roadmap, not implementation status).

---

## weapons_engagement_impl.md

### Verified
- All `Missile` fields (`guidance_delay_s`, `guidance_update_period_s`, `launch_time`, `last_guidance_time`, `seeker_fov_deg`, `seeker_lock_range`, `nav_gain`, `turn_rate`) — verified in `src/components/combat/weapon.h`

### Mismatches
- **Claim**: "Missile parameter setup: `src/core/simulation_kernel.cpp`"
  **Reality**: Actual: `src/core/engine/simulation_kernel.cpp` and `src/core/engine/simulation_kernel_weapon_api.cpp`
  **Severity**: P1

- **Claim**: "Guidance logic: `src/models/default_guidance_model.cpp`"
  **Reality**: Actual: `src/models/weapons/default_guidance_model.cpp`
  **Severity**: P1

- **Claim**: "Guidance system: `src/systems/guidance_system.h`"
  **Reality**: Actual: `src/systems/combat/guidance_system.h`
  **Severity**: P1

- **Claim**: "Data structures: `src/components/weapon.h`"
  **Reality**: Actual: `src/components/combat/weapon.h`
  **Severity**: P1

---

## models/hierarchical_moe_execution_policy.md

### Verified
- `SquashedMultiInputPolicy`, `HierarchicalMoEExecutionPolicy` — verified in `python/rl/policy_algo/policies.py`
- `MissionCommand`, `TaskOrder`, `LeaderIntent` fields — all verified via bindings.

No mismatches found.

---

## Summary

### P1 (Wrong paths or claimed features that do not exist): 11 items
### P2 (Partially wrong paths): 2 items
### P3 (Misleading labels): 1 item
