# Air Combat 1v1 Training Entries

This directory holds maintained in-progress `1v1` air-combat execution configs.

## Scope

- Scenario pairings for this line are:
  - [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
    - Used by the scripted-red `F-16C` smoke and 8k probe entries.
  - [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
    - Used by the Stage-0 drone weapon-employment reactive and temporal world-batch probe entries.
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json)
    - Used by the Stage-1 BVR non-maneuvering target world-batch probe entry.
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json)
    - Used by the Stage-1 M1 hybrid shaped training probe after the live damage chain and hybrid action interface are both available.
- Current baseline is:
  - Blue learner: `F-16C_Block50`
  - Early curriculum target: unarmed `MQ-9_Reaper` surrogate for Stage 0 and Stage 1
  - Scripted-red smoke opponent: scenario-declared `F-16C_Block50`
  - Policy architecture: `HierarchicalMoEExecutionPolicy`
- Stage-2 and Stage-3 `scenarios/air_combat/1v1` files are maintained curriculum scenarios, but no active training config in this directory is paired to them yet.

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

- [air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json)
  - Stage-0 drone weapon-employment probe using the single-frame `TransformerExtractor` reactive baseline.
  - Use it to inspect basic fire flow, repeated launches, reward, and termination behavior.

- [air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json](air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json)
  - Stage-0 M1 temporal HMoE probe.
  - Enables `temporal_history_len=16` plus `TemporalTransformerExtractor` while keeping the main hyperparameters close to the reactive baseline.
  - This is a validation entry before Path C, not the final sequence-native causal policy.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json)
  - Stage-1 BVR-like range-expansion probe against the unarmed non-maneuvering target.
  - Keeps the same HMoE execution surface as Stage 0 while increasing rollout horizon pressure with longer contact persistence and missile time-of-flight.
  - This is the first post-damage-model continuation entry; it is still an active probe, not a fixed-fire win gate or frozen baseline.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json)
  - Stage-1 M1 temporal HMoE probe.
  - Enables `temporal_history_len=16` plus `TemporalTransformerExtractor` while keeping the main hyperparameters close to the Stage-1 reactive baseline.
  - Used after restoring the live damage chain to compare whether the temporal window improves repeat-fire, launch interval, and fixed diagnostic metrics.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json)
  - Stage-1 M1 action-interface probe using `action_mode=air_combat_hybrid_v1`.
  - Flight controls remain continuous, while radar / TMS / master-arm / fire / weapon-select use policy-side hybrid action semantics.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json)
  - Stage-1 M1 action-interface plus temporal probe.
  - Used to compare action-reachability repair separately from observation-window temporal evidence.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json)
  - Stage-1 M1 hybrid shaped training probe.
  - Uses the training-shaped Stage-1 scenario with stable-flight shaping and first-release reward while preserving the canonical Stage-1 geometry and weapon/damage runtime.
  - Enables a narrow stable-flight residual wrapper only on flight-control axes `[0, 1, 2, 3]`; hybrid combat commands remain unlocked and unsnapped.
  - This is the maintained entry for checking whether the repaired action interface can recover release exploration before moving to longer M1 evidence runs.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json)
  - Stage-1 M1 hybrid temporal shaped comparison probe.
  - Uses the same training-shaped scenario, stable-flight residual wrapper, and low initial exploration noise as the hybrid shaped entry.
  - Only adds `temporal_history_len=16` plus `TemporalTransformerExtractor` so repeated launches, early launches, and launch intervals can be rechecked under the recovered S1 training surface.

## Design Notes

- These smoke entries are intentionally non-visual.
  - The goal is to verify the combat task contract and runtime chain first, not visual throughput.
- These smoke entries use the current HMoE mainline architecture directly.
  - `1v1` does not keep a separate shared-policy active entry as its primary maintained path.
- Current `1v1` smoke still uses `mission_obs_mode=basic`.
  - So the HMoE policy is active, but the maintained route semantics exposed to the policy are still minimal.
  - In current smoke logs this means routing stays on the navigation family/subexpert, which is acceptable for chain validation but not yet a fully differentiated combat-routing setup.
- The raw `full`, hybrid, and temporal smoke entries intentionally do not enable the maintained scripted-residual action wrapper.
  - The shaped hybrid and hybrid temporal shaped training probes are the exceptions: they blend only the first four flight-control axes against stable flight and leave radar / master-arm / fire / weapon-select policy commands untouched.
  - For first `1v1` smoke we still want the learner to retain the raw action surface.
- These entries are not acceptance/frozen baselines yet.
  - Promote only after `1v1` reward/termination/eval behavior is stable enough to compare across runs.
- Temporal entries only expose short history to the policy.
  - They do not change missile physics, ammunition, cooldown, or environment-side tactical memory.
- Hybrid entries only change the training-facing action interface.
  - They expose `fire_weapon` as policy-facing pulse/effective transport semantics; they do not change the weapon-release kernel, launch envelope, or damage model.
