# M1 Air-Combat Action Interface Split

Status: `2026-06-02`, `accepted`. The `air_combat_hybrid_v1` training action
interface slice is implemented and passes focused tests plus short scenario
probes; learned `1v1` policy acceptance and M2 release are still not accepted.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Temporal HMoE Policy Plan](../temporal_hmoe_policy_plan_20260525.md)
- [M1 Temporal Window HMoE](../m1_temporal_window_hmoe/README.zh.md)
- [A3 C2/ROE Release Discipline](../../air_combat/a3_c2_roe_release_discipline/README.md)
- [Pilot Action Contract](../../../standards/air/act.md)
- Current action adapter:
  [actions.py](../../../../gym_envs/universal_env_parts/actions.py)
- Current world-batch runtime:
  [world_batch_vec_env.py](../../../../python/rl/runtime/world_batch_vec_env.py)
- Current HMoE policy:
  [policies.py](../../../../python/rl/policy_algo/policies.py)

## Purpose

Create a bounded M1 follow-on for the action-interface problem exposed by the
stage-0 / stage-1 air-combat probes: continuous `Box` dimensions are currently
used for both flight controls and combat switches. The runtime latch prevents
unbounded held-trigger missile spam, but the policy still has to discover
binary combat commands through discontinuous thresholds.

This subproject moves the `1v1` air-combat training surface toward a hybrid
interface: continuous flight axes stay continuous, while radar / target-management
switches, master-arm, weapon select and weapon release become explicit discrete
or pulse commands at the policy/action-adapter boundary.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| `full` action mode | implemented | `make_action_space("full")` is a 17D `Box`; `build_pilot_action()` thresholds switch dimensions. | Maintained runtime surface, but not training-friendly for sparse switch discovery. |
| `air_combat_hybrid_v1` action mode | accepted | 12D flat `Box` transport with policy-side continuous flight axes, Bernoulli switches/pulses and categorical weapon select. | Kept as flat transport for SB3/runtime compatibility; not a Gym `Dict` action-space migration. |
| Weapon release latch | implemented | `PilotWeaponReleaseState` consumes a held trigger after one successful release. | Prevents repeated successful launches while held; does not make continuous threshold actions a good policy interface. |
| M1 temporal history | accepted | Hybrid runtime records the effective transport action in `proprio` / `proprio_history`; raw policy intent is retained only for rising-edge detection. | Whether temporal windows improve learned fire/release remains follow-on M1-A4 evidence. |
| Multi-timescale wrapper | implemented support | `MultiTimescaleActionController` supports hold, snap and hysteresis for selected dimensions. | Still operates over a flat continuous `Box`; useful as a transition probe, not a true hybrid action distribution. |
| HMoE PPO policy | accepted | `HierarchicalMoEExecutionPolicy(..., hybrid_action_spec="air_combat_hybrid_v1")` emits 19 params and computes joint log-prob. | Tanh-squashed Gaussian axes have no reliable closed-form entropy; PPO keeps the `-log_prob` sampled entropy estimate. |

## Scope

In scope:

- Define an air-combat action contract that separates continuous flight controls
  from switch, selector and pulse semantics.
- Add a transition action adapter or action mode for `1v1` probes, with explicit
  `fire_weapon` pulse behavior and documented `proprio` semantics.
- Add or extend policy support so combat switches are sampled as Bernoulli /
  categorical commands rather than learned through raw `> 0.5` Gaussian tails.
- Wire the maintained single-env compatibility path and the maintained
  `WorldBatchVecEnv` training path consistently.
- Add active air-combat probe configs and focused tests that compare `full`
  against the new action interface under the same stage and seed rules.

Out of scope:

- Missile physics, guidance, fuze, damage, ammo or cooldown changes.
- Tactical memory boards inside `src/systems/combat`.
- Declaring a trained `1v1` policy accepted.
- Starting M2 sequence-native PPO before M1 evidence review.
- Broad cockpit HOTAS modeling beyond the current `PilotAction` contract.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze the action-interface problem and distinguish it from missile-release kernel behavior. | M1-A4 action-stat evidence and held-trigger runtime tests exist. | README and task cluster define in/out scope. | pass |
| `P1 Source Audit` | Map every action-mode, config, runtime, policy and test touchpoint. | `P0` accepted. | Patch list and risk map are recorded. | pass |
| `P2 Transition Adapter` | Provide a low-risk probe path that removes held threshold ambiguity without changing PPO distribution yet. | `P1` accepted. | Focused tests show pulse/effective-action/proprio behavior is deterministic. | pass |
| `P3 Hybrid Policy` | Add a policy-side hybrid action distribution or equivalent joint log-prob flat transport. | `P2` evidence available. | HMoE PPO can train with discrete switch / selector heads and continuous flight axes. | pass |
| `P4 Air-Combat Probe` | Add stage-0 / stage-1 configs and diagnostics comparing `full`, transition adapter and hybrid policy. | `P3` implementation passes smoke tests. | Same-seed probes report launch reachability, invalid fire attempts and repeated launch intervals. | pass |
| `P5 Closure` | Decide whether the repaired action interface should be folded into M1 evidence before M2 release vote. | `P4` evidence available. | Acceptance or held residuals recorded and parent model README synced. | accepted |

## Task Clusters

- Task cluster plan:
  [m1_action_interface_split_task_clusters_20260602.md](m1_action_interface_split_task_clusters_20260602.md)
- Chinese companion:
  [m1_action_interface_split_task_clusters_20260602.zh.md](m1_action_interface_split_task_clusters_20260602.zh.md)

## Outputs And Evidence

- Updated action-interface documentation for air-combat training.
- Focused action-adapter tests for switch, selector and pulse behavior.
- Runtime tests covering `UniversalEnv` compatibility and `WorldBatchVecEnv`.
- HMoE policy tests if the hybrid distribution route is implemented.
- Stage-0 / Stage-1 active air-combat probe configs and evidence notes.
- Current checkpoint:
  [m1_action_interface_split_current_status_20260602.md](m1_action_interface_split_current_status_20260602.md)
- Acceptance record:
  [m1_action_interface_split_acceptance_20260602.md](m1_action_interface_split_acceptance_20260602.md)

Evidence run:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_air_combat_active_training_entries.py
# 40 passed

git diff --check -- docs/task/model docs/standards/air gym_envs python examples/config/training/active/air_combat tests train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed; final_model.zip saved

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_hybrid_range_gate_report.json --csv_out /tmp/cmo_m1_hybrid_range_gate_trace.csv
# pass; fire_attempt_count=1, release_count=1, invalid_fire_attempt_count=0, damage_report_count=1
```

## Acceptance Gate

This subproject can be marked accepted only when:

- `fire_weapon` is exposed to training as an explicit pulse or discrete command,
  not merely as an ambiguous continuous threshold in the accepted probe surface.
- Radar / master-arm / target-management switch semantics are documented and
  tested for reset, held and repeated-command behavior.
- `proprio` / temporal history semantics are documented for the new action
  interface.
- The maintained world-batch path and training bootstrap accept the new surface.
- At least one stage-0 or stage-1 short probe can report action reachability,
  launch attempts and repeated-release metrics under the new interface.
- The docs still refuse missile-physics, damage or tactical-memory overclaims.

## Residuals And Next Steps

- M1-A4 evidence remains insufficient to release M2 until action reachability is
  separated from temporal-memory evidence.
- The 32-step smoke model deterministic probe still does not fire:
  `fire_attempt_count=0`, `release_count=0`, ending with `failfast_deep_stall`.
  That proves action-interface reachability, not learned-policy quality.
- The 65k shaped hybrid follow-up restores training flight stability:
  deterministic final-model probe reaches `combat_timeout` with no release, and
  stochastic final-model probes can release but still fire early/repeatedly.
- Tactical memory for "one missile already in flight against this target" now
  routes first through A3 shot policy, pending assessment, salvo authorization,
  and reattack authorization. Only unexplained repeated fire after those
  constraints are observable should return to a later policy/memory package.

## Archive

No archived records exist yet. Historical records should move to `archive/` only
after a current README or acceptance document tells future agents where to start.
