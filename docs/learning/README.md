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
- [Model task area](../task/model/README.md): active experiments, evidence,
  dispatch, and held/pass decisions. Task labels such as M3-S1 and M3-S2 do not
  rename the reusable implementation API.
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

## Open Work Routes

- [Hierarchical MoE execution policy](work/issues/hierarchical_moe_execution_policy.md): maintained design direction, not an implementation standard.
- [Reinforcement learning and self-play](work/issues/rl_selfplay.md): draft roadmap.

Both pages remain planning inputs under `work/issues`; neither path grants
implementation authority.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for future learning standards, references, active work, issues, and reviews.
