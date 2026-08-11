# Air Combat 1v1 Training Entries

This directory holds maintained in-progress `1v1` air-combat execution configs.

## Scope

- Policy/model terminology follows the
  [Policy Execution Architecture Baseline](../../../../../docs/learning/standards/policy_execution_architecture.md).
  A-stage and M3 labels below identify historical task/evidence lanes; current
  config keys and reusable model APIs remain role-based.
- Scenario pairings for this line are:
  - [air_combat_1v1_headon_sensor_smoke_v1.json](../../../../../scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json)
    - Used by the scripted-red `F-16C` smoke and 8k probe entries.
  - [air_combat_1v1_stage0_drone_weapon_employment_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json)
    - Used by the Stage-0 drone weapon-employment reactive and temporal world-batch probe entries.
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json)
    - Used by the Stage-1 BVR non-maneuvering target world-batch probe entry.
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json)
    - Used by the Stage-1 M1 hybrid shaped training probe after the live damage chain and hybrid action interface are both available.
  - [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json)
    - Used by the additive Stage-1 A3 C2/ROE hybrid shaped and temporal shaped probes; legacy M1 baseline entries remain on `mission_obs_mode=basic`.
  - [air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json](../../../../../scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json)
    - Used by the A1 Stage-2 C2/ROE event-window continuation entry, historically tracked as M3-S2; the goal is to transfer accepted Stage-1 release discipline to the maneuvering-red, red-unarmed scenario.
    - As of DCR-D, explicitly opts in low-weight damage consequence reward terms for synthetic training shaping only.
- Current baseline is:
  - Blue learner: `F-16C_Block50`
  - Early curriculum target: unarmed `MQ-9_Reaper` surrogate for Stage 0 and Stage 1
  - Scripted-red smoke opponent: scenario-declared `F-16C_Block50`
  - Policy architecture: `HierarchicalMoEExecutionPolicy`
- The canonical Stage-2 and Stage-3 `scenarios/air_combat/1v1` files remain maintained curriculum scenarios. This directory currently pairs only the Stage-2 C2/ROE training-shaped entry; Stage-3 still has no active training config.

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

- [air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json](air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json)
  - 32k scripted-red baseline probe on the maintained `WorldBatchVecEnv` path.
  - Pairs with the TG-P7 32k proxy entry so the default F-16 damage database remains the same-budget control path.

- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json](air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json)
  - Opt-in TG-P7 target-geometry proxy probe on the maintained `WorldBatchVecEnv` path.
  - Uses `runtime.database_path` to load the R3 proxy database while leaving the default `examples/config/database` F-16 damage model unchanged.
  - Carries the `A2_TARGET_GEOMETRY_PROXY_F16C_R22` metadata so geometry-proxy training evidence stays separate from default damage-model authority.

- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json](air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json)
  - TG-P7 32k opt-in proxy training entry on the maintained `WorldBatchVecEnv` path.
  - Keeps the same policy, environment, and hyperparameter surface as the 32k baseline except for `runtime.database_path` and TG-P7 proxy metadata.
  - Used for longer post-R5 training stability and reward/policy diagnostics without replacing the default damage database.

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

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json)
  - Stage-1 A3 C2/ROE hybrid shaped probe using `mission_obs_mode=air_combat_c2_roe_v1`.
  - Uses the C2/ROE training-shaped Stage-1 scenario with an explicit single-shot-then-assess command state.
  - This is an additive partial probe entry while reward/process metrics are still owned by the A3 reward/diagnostics stream.
  - As of A4, this entry uses the five-family HMoE route surface `[3, 2, 3, 1, 3]`, where the fifth family is `combat_weapons`.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json)
  - Stage-1 A3 C2/ROE hybrid temporal shaped comparison probe using `mission_obs_mode=air_combat_c2_roe_v1`.
  - Pairs with the A3 C2/ROE reactive shaped entry and only adds `temporal_history_len=16` plus `TemporalTransformerExtractor`.
  - This is the maintained next entry for rerunning reactive/temporal learned-policy comparisons after post-launch mission observation became dynamic.
  - As of A4, it shares the same `combat_weapons` family as the reactive C2/ROE shaped probe; the rejected pulse-prior trial is not retained.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json)
  - Stage-1 A6 deadline-bootstrap probe using the same C2/ROE temporal shaped surface.
  - Keeps legality owned by A3/A5 event masks and state transitions.
  - Replaces the short decaying curriculum with a sustained deadline target after an open-window age threshold, so it is evidence for A6 re-scope rather than a new M2 release.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json)
  - Stage-1 A6-EVT-K event-head optimization probe using the same deadline-bootstrap C2/ROE temporal shaped surface.
  - Adds `hybrid_event_head_lr_scale=10.0` as a dedicated zero-initialized `hold/fire_once` event-logit update lane.
  - It tests optimizer ownership after the event-head update-strength audit; it does not weaken A3/A5 masks or release M2.
  - The 32k A6-EVT-K probe crossed deterministic argmax and preserved one-shot discipline, but A6 remains held on launch-window timing quality.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json)
  - Stage-1 A6-EVT-L launch-window timing-contract probe using the same event-head C2/ROE temporal shaped surface.
  - Separates legal authorization from quality-window launch labels with policy-observed contact range/track age and legal-window age.
  - Early accepted releases become negative labels; deadline/curriculum positives are gated by the launch window.
  - It is an implementation/evidence entry for the next short probe, not M2 release, doctrine, missile-authority, or Pk evidence.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_shaped_world_batch_probe_v1.json)
  - Stage-1 A7 event-credit probe using the same C2/ROE temporal shaped and launch-window gate.
  - Keeps A6 hazard loss disabled and trains the zero-initialized `hybrid_event_credit_head` with value credit plus event-logit delta alignment.
  - Includes `event_credit_shadow_quality_weight=1.0` for the A7-EVC-J shadow-quality target repair path.
  - As of A7-EVC-M, enables projected legal-open credit with
    `event_credit_legal_projection_enabled=true`,
    `event_credit_projection_value_coef>0`, and
    `event_credit_projection_delta_align_coef>0`.
  - As of A7-EVC-V, enables the protected online credit update contract with
    `event_credit_separate_update_enabled=true`,
    `event_credit_separate_update_max_grad_norm=0.5`, and
    `event_credit_delta_align_positive_only=true`.
  - Keeps A3/A5 legality masks and one-shot state-machine authority unchanged.
  - It was used by A7-G r3 and A7-EVC-J repair evidence; both are valid but held because deterministic releases remain `0` and quality-window advantage stays negative.
  - It is now the maintained entry for A7-EVC-N short projection learned evidence after M focused gates.
  - It is not M2 release, doctrine, missile-authority, or Pk evidence, and focused projection tests still do not count as behavior acceptance.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_state_completed_world_batch_probe_v1.json)
  - Stage-1 A7 explicit state-completion probe using `mission_obs_mode=air_combat_c2_roe_v2`.
  - Keeps the A7/R event-credit hyperparameters unchanged while exposing current legal-open age, launch-window readiness, quality-window readiness, target range, and target track age in the mission observation.
  - Includes the A7-EVC-V protected credit update contract:
    separate credit-head value updates, positive-only delta alignment, and a
    separate clip budget.
  - The 32k S probe completed as held evidence: focused tests passed, open-window fire probability rose, deterministic probing still recorded `0` releases, and quality-window advantage remained negative.
  - It is a pre-M2 structural observability experiment; it does not release sequence-native M2, doctrine, missile-authority, or Pk evidence.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1.json)
  - Stage-1 grouped-stopping short probe, historically tracked as M3-S1, using the A7 explicit state-completion observation surface.
  - Opens the independent `stopping_head` and `grouped_stopping_*` auxiliary objective while keeping A7 coefficients and A3/A5 legality masks unchanged.
  - Uses an 8k budget for validation evidence, not a promoted formal training run.
  - This entry can prove stopping-boundary movement only; executable fire timing remains held until the stopping head is connected to or compared against the hybrid event action path.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1.json)
  - Stage-1 direct fire-boundary short probe, historically tracked as M3-S2, using the A7 explicit state-completion observation surface.
  - Keeps HMoE and `air_combat_hybrid_v1`, but makes `hybrid_event_head` the only executable hold/fire owner for this config; both stopping and window-classifier event adapters are explicitly disabled.
  - Uses the grouped sidecar legal/quality rows as boundary labels, computes loss on the final executable fire-minus-hold logit, and restricts the dedicated auxiliary update to `hybrid_event_head` parameters.
  - Applies explicit calibration: non-quality legal rows are capped at a negative ceiling while quality-window rows are pushed toward a positive floor.
  - Uses support-preserving collection, including quality-window hold preservation, so the sidecar can see the complete legal-to-quality transition before behavior acceptance is claimed.
  - Uses an 8k budget for validation evidence; behavior acceptance still requires learned-policy release probes.

- [air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1.json](air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1.json)
  - A1 Stage-2 C2/ROE event-window continuation entry, historically tracked as M3-S2, using the maneuvering-red, red-unarmed training-shaped Stage-2 scenario.
  - Reuses the Stage-1 direct fire-boundary owner and `air_combat_c2_roe_v2` observation surface without weakening A3/A5 legality or the one-shot state machine.
  - The `2026-06-08` 8k init-from-Stage-1 short train preserved one accepted authorized release in deterministic and stochastic single-episode probes, but had no effects/damage/kill; it is a Stage-2 training entry, not stage acceptance.
  - The paired Stage-2 training-shaped scenario now explicitly enables low-weight damage consequence shaping:
    `air_combat_damage_consequence_shaping_enabled=true`,
    `air_combat_target_damage_consequence_scale=0.05`,
    `air_combat_self_damage_consequence_scale=0.02`, and
    `air_combat_damage_consequence_delta_clip=0.5`.
  - Those terms are synthetic training feedback from observed consequence state only. They do not close launch behavior, assert real Pk/kill authority, change weapon or damage runtime, or count as Stage-2 acceptance evidence.

- [air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json](air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json)
  - Stage-1 M1 hybrid temporal shaped comparison probe.
  - Uses the same training-shaped scenario, stable-flight residual wrapper, and low initial exploration noise as the hybrid shaped entry.
  - Only adds `temporal_history_len=16` plus `TemporalTransformerExtractor` so repeated launches, early launches, and launch intervals can be rechecked under the recovered S1 training surface.

## Design Notes

- These smoke entries are intentionally non-visual.
  - The goal is to verify the combat task contract and runtime chain first, not visual throughput.
- These smoke entries use the current HMoE mainline architecture directly.
  - `1v1` does not keep a separate shared-policy active entry as its primary maintained path.
- Current legacy `1v1` smoke and M1 baseline entries still use `mission_obs_mode=basic`.
  - So the HMoE policy is active, but the maintained route semantics exposed to the policy are still minimal.
  - In current smoke logs this means routing stays on the navigation family/subexpert, which is acceptable for chain validation but not yet a fully differentiated combat-routing setup.
  - The A3/A4 C2/ROE probes are intentionally separate and additive; do not use them as evidence that legacy M1 baselines changed observation mode.
  - The dedicated `combat_weapons` HMoE family is only reachable when the policy sees `mission_obs_mode=air_combat_c2_roe_v1`.
- The raw `full`, hybrid, and temporal smoke entries intentionally do not enable the maintained scripted-residual action wrapper.
  - The shaped hybrid and hybrid temporal shaped training probes are the exceptions: they blend only the first four flight-control axes against stable flight and leave radar / master-arm / fire / weapon-select policy commands untouched.
  - For first `1v1` smoke we still want the learner to retain the raw action surface.
- These entries are not acceptance/frozen baselines yet.
  - Promote only after `1v1` reward/termination/eval behavior is stable enough to compare across runs.
- Temporal entries only expose short history to the policy.
  - They do not change missile physics, ammunition, cooldown, or environment-side tactical memory.
- Hybrid entries only change the training-facing action interface.
  - They expose `fire_weapon` as policy-facing pulse/effective transport semantics; they do not change the weapon-release kernel, launch envelope, or damage model.
