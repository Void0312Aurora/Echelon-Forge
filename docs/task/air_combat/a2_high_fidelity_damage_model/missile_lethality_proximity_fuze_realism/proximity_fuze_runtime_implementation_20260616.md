# Proximity Fuze Runtime Implementation Result

Status: `2026-06-16` PF-R4 pass / focused runtime implementation complete.

Chinese companion:
[proximity_fuze_runtime_implementation_20260616.zh.md](proximity_fuze_runtime_implementation_20260616.zh.md).

## Scope Implemented

This PF-R4 slice implements the approved non-authoritative surrogate contract as
runtime explainability, not as real weapon calibration.

Implemented:

- Added terminal negative reasons:
  - `outside_sensor_window`
  - `target_not_detected`
- Added fuze sensor and detection evidence to `FuzeEvaluationEvent`,
  `EffectsEvent`, missile debug runtime state, Python bindings, and diagnostic
  chain rows.
- Added a proximity-fuze surrogate evidence step before trigger sampling:
  - sensor opportunity source and score;
  - terminal-track validity;
  - target detection source, confidence, and threshold;
  - detected/not-detected flag;
  - detonation point source;
  - mechanism coverage score.
- Preserved no-load behavior for no detonation, no terminal track,
  outside-sensor-window, and target-not-detected outcomes.
- Kept contact and timed fuze paths explicit.
- Kept the existing detonation probability surface mostly compatible after
  detection succeeds; the new detection evidence is a gate and diagnostic
  explanation, not a calibrated Pk model.
- Updated diagnostic row schema to version `7` so downstream CSV/JSON consumers
  can see the new fuze evidence columns.

## Files Touched

- [../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)
- [../../../../../src/components/combat/common/weapon_common.h](../../../../../src/components/combat/common/weapon_common.h)
- [../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- [../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- [../../../../../src/core/engine/weapon_launch_adapter.h](../../../../../src/core/engine/weapon_launch_adapter.h)
- [../../../../../src/interfaces/python/bindings_runtime.cpp](../../../../../src/interfaces/python/bindings_runtime.cpp)
- [../../../../../src/interfaces/python/bindings_core.cpp](../../../../../src/interfaces/python/bindings_core.cpp)
- [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h)
- [../../../../../tools/diagnostics/lethality_chain_contract.py](../../../../../tools/diagnostics/lethality_chain_contract.py)
- [../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)
- [../../../../../tests/runtime/air_combat/weapon_guidance_realism/fuze.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/fuze.py)
- [../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py](../../../../../tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py)
- [../../../../../tests/runtime/bindings/test_bindings_engagement_surface.py](../../../../../tests/runtime/bindings/test_bindings_engagement_surface.py)

## Validation

All commands used the project virtual-environment wrapper:
`.\tools\maintenance\cmo_env.ps1`.

Passed:

```powershell
cmake --build build-local-win --target ef_py -j2
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_continuous_rod_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_fuze_no_detonation_event_gate.py tests/runtime/air_combat/test_live_detonation_event_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/air_combat/test_diagnostics_process_probe_lethality.py tests/runtime/air_combat/test_diagnostics_process_probe_snapshot.py tests/runtime/air_combat/test_diagnostics_process_probe_summary.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/training/test_fire_timing_fault_localization_contracts.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/runtime/bindings/test_bindings_engagement_surface.py tests/runtime/engagement/test_engagement_contract_shape.py
```

Observed pass counts:

- build: pass, with pre-existing unused-variable warnings;
- launch/guidance/fuze: `36 passed, 4 subtests passed`;
- continuous rod surface: `14 passed`;
- fuze no-detonation and live detonation event gates: `2 passed`;
- diagnostics process probe suite: `34 passed`;
- training fault-localization contracts: `19 passed`;
- binding and engagement contract shape: `23 passed`.

## Residuals

- PF-R4 does not claim real fuze thresholds, real Pk, weapon-specific lethality,
  or deterministic fuze authority.
- The broader `test_warhead_and_component_damage.py` suite was sampled and
  showed failures dominated by current component-geometry identity and primary
  component expectations. Those failures are not used as PF-R4 acceptance
  evidence and should be handled in a geometry/test-baseline follow-up rather
  than hidden inside the fuze surrogate slice.
- PF-R5 matrix validation is now complete as a focused surrogate check; its
  residual is that live guidance keeps actual miss distance in a narrow band,
  so initial launch offsets are not pure detonation-position symmetry tests.

## Decision

PF-R4 is complete as a focused implementation and diagnostic-export slice.
Runtime acceptance remains limited to the tested surrogate evidence contract.
PF-R5 is now closed as surrogate matrix validation with residuals, not as real
fuze calibration or Pk authority.
