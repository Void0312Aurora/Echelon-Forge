# Learning Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/learning/README.md`
Owner: `learning and experimentation`
Last verified: `2026-08-08`

This target area owns reinforcement learning, policy/model architecture,
training, evaluation protocols, world-model work, and experiment definitions.
It does not own mission-domain semantics, runtime action legality, physics,
weapon effects, or the acceptance status of an active experiment.

## Maintained Authority

- [Policy Execution Architecture Baseline](standards/policy_execution_architecture.md):
  the maintained standard for executable policy paths, auxiliary mechanisms,
  losses, rollout labels, and evidence boundaries.
- [Air Pilot Action Contract](../domains/air/standards/pilot_action_contract.md):
  owner of `air_combat_hybrid_v1`, `event_action_mask`, `fire_once`, and runtime
  trigger interpretation.

## Current Implementation Map

- Policy and heads: [policies.py](../../python/rl/policy_algo/policies.py)
- PPO composition and rollout/update orchestration:
  [ppo_adaptive_kl.py](../../python/rl/policy_algo/ppo_adaptive_kl.py)
- Grouped stopping loss and update:
  [grouped_stopping.py](../../python/rl/policy_algo/grouped_stopping.py),
  [_grouped_stopping_mixin.py](../../python/rl/policy_algo/_grouped_stopping_mixin.py)
- Event-window, fire-boundary, and window-classifier updates:
  [_event_window_mixin.py](../../python/rl/policy_algo/_event_window_mixin.py)
- Mission-observation assembly:
  [mission_observation.py](../../gym_envs/scenario_loader/mission_observation.py)
- Active air-combat training entries:
  [training configuration index](../../examples/config/training/active/air_combat/README.md)

Current reusable names are role-based, including `stopping_head`,
`window_classifier_head`, `grouped_stopping_*`, `event_window_*`, and
`fire_boundary_*`. Historical `M3-S1` / `M3-S2` labels remain valid in task,
mechanism-ID, and metric namespaces such as `m3s1/` and `m3s2/`; they are not
general implementation prefixes.

## Active Work

- [Air-combat 1v1 realism gradient](work/active/air_combat_1v1_realism_gradient/README.md)
- [Damage-consequence reward surface](work/active/air_combat_damage_consequence_reward/README.md)
- [Temporal-window HMoE](work/active/temporal_window_hmoe/README.md)

These packages own scoped execution status only. They do not redefine Air
mission semantics, effects physics, or the policy-architecture standard.

## Open Work Routes

- [Hierarchical MoE execution policy](work/issues/hierarchical_moe_execution_policy.md): maintained design direction, not an implementation standard.
- [Reinforcement learning and self-play](work/issues/rl_selfplay.md): draft roadmap.
- [Temporal policy roadmap](work/issues/temporal_policy_roadmap.md)
- [Causal-transformer HMoE](work/issues/causal_transformer_hmoe/README.md)
- [Launch-window label imbalance](work/issues/launch_window_label_imbalance/README.md)
- [HMoE hierarchical computation gap](work/issues/hmoe_hierarchical_computation_gap/README.md)
- [Policy hold baseline drift](work/issues/policy_hold_baseline_drift/README.md)
- [Cooperative training foundation and performance](work/issues/multi_agent_cooperative_training_foundation_and_performance_plan.md)
- [Cooperative execution pipeline findings](work/issues/p8_cooperative_execution_pipeline_findings_and_plan.md)

These pages remain planning inputs under `work/issues`; no path grants
implementation authority.

## Retained Reviews

- [Air-combat action-interface split](reviews/air_combat_action_interface_split_20260602/README.md)
- [Optimal-stopping model selection](reviews/optimal_stopping_model_selection_20260605/README.md)
- [Grouped-stopping contract](reviews/grouped_stopping_contract_20260605/README.md)

These are dated accepted or retained evidence packets, not active work queues.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for future learning standards, references, active work, issues, and reviews.
