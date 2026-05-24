# Air Combat 1v1 Training Entries

This directory holds maintained in-progress `1v1` air-combat execution configs.

## Scope

- Scenario pairing for this line is:
  - [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
- Current baseline is:
  - Blue learner: `F-16C_Block50`
  - Red opponent: scenario-declared scripted `F-16C_Block50`
  - Policy architecture: `HierarchicalMoEExecutionPolicy`

## Entries

- [air_combat_1v1_f16c_scripted_red_smoke_v1.json](air_combat_1v1_f16c_scripted_red_smoke_v1.json)
  - Minimal bootstrap smoke on the standard `execution` vec-env path.
  - Uses the maintained HMoE policy surface directly, not a shared-policy fallback.

- [air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json)
  - Matching smoke entry on the maintained default `WorldBatchVecEnv` path.
  - Use this when you want to verify the scripted-red opponent and HMoE policy also advance correctly through the batch runtime path.

- [air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json)
  - Short HMoE training probe on the maintained `WorldBatchVecEnv` path.
  - Runs beyond smoke length while staying small enough for frequent diagnostics.
  - Use this before any 32k/64k resume ramp to check whether early termination is still dominated by flight-stability artifacts.

## Design Notes

- These smoke entries are intentionally non-visual.
  - The goal is to verify the combat task contract and runtime chain first, not visual throughput.
- These smoke entries use the current HMoE mainline architecture directly.
  - `1v1` does not keep a separate shared-policy active entry as its primary maintained path.
- Current `1v1` smoke still uses `mission_obs_mode=basic`.
  - So the HMoE policy is active, but the maintained route semantics exposed to the policy are still minimal.
  - In current smoke logs this means routing stays on the navigation family/subexpert, which is acceptable for chain validation but not yet a fully differentiated combat-routing setup.
- These smoke entries intentionally do not enable the maintained scripted-residual action wrapper.
  - The current stable-flight residual presets lock several switch dimensions that are useful in air combat, including weapon-related controls.
  - For first `1v1` smoke we want the learner to retain the raw `full` action surface.
- These entries are not acceptance/frozen baselines yet.
  - Promote only after `1v1` reward/termination/eval behavior is stable enough to compare across runs.
