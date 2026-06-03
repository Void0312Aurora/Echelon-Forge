# A4 Authorized First-Shot Training Signal Task Clusters

Status: `2026-06-03` finite task-cluster plan for
[README.md](README.md).

## Boundary Decision

A4 may change reward shaping, maintained S1 C2/ROE probe knobs, focused tests,
and documentation needed to make an authorized first shot trainable. A4 may not
change missile physics, damage authority, Pk/fuze authority, ammunition runtime,
M2, self-play, or real-world BVR doctrine claims.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A4-SIG-A Boundary` | main thread | n/a | Create A4 scope, phase plan, and residual map. | `docs/task/air_combat/a4_authorized_first_shot_training_signal/**`, parent air-combat README links | Reopening A3 accepted scope or M2 | Link/readability check | README and cluster plan exist and parent docs link them. | First, serial | 1 | pass |
| `A4-SIG-B Reward Surface` | main thread | n/a | Add configurable authorized weapon-chain reward terms. | `gym_envs/scenario_loader/reward_runtime/air_combat.py`, `tests/runtime/air_combat/test_air_combat_reward_surface.py` | Silent fire suppression, physics or ammo changes | `pytest tests/runtime/air_combat/test_air_combat_reward_surface.py` | Terms are gated by authorization and single-shot state. | After A | 2 | pass |
| `A4-SIG-C Scenario Probe` | main thread | n/a | Enable conservative shaping knobs in maintained S1 C2/ROE training-shaped scenario. | `scenarios/air_combat/1v1/*c2_roe_training_shaped*.json`, `tests/training/test_air_combat_active_training_entries.py` | Changing M1 basic baselines | Active-entry pytest | Config test proves knobs are present only on A3/A4 probe. | After B; can run with docs | 2 | pass |
| `A4-SIG-D Short Evidence` | main thread | n/a | Run bounded post-change learned-policy probe. | `docs/task/air_combat/a4_authorized_first_shot_training_signal/*probe*.md`, no `experiments_tmp` staging | Claiming acceptance from one run | Train/probe commands recorded | Deterministic/stochastic fire/release metrics are compared to A3 evidence. | After B/C tests | 2 | pass, held outcome |
| `A4-SIG-E Routing Review` | main thread | n/a | Decide whether HMoE needs an air-combat weapons route. | `python/rl/policy_algo/hmoe_routing.py`, `python/rl/policy_algo/policies.py`, `train.py`, C2 configs, related tests/docs | Large policy rewrite without evidence | Routing, policy, and active-entry tests | A combat-weapons route is tested and documented. | After D | 2 | pass |
| `A4-SIG-F Binary Diagnostics` | main thread | n/a | Expose binary action logits/probabilities and test one bounded opportunity-penalty reward trial. | `python/rl/policy_algo/policies.py`, `python/training_callbacks.py`, `tools/diagnostics/air_combat_stage0_process_probe.py`, reward/config tests, A4 evidence docs | Treating reward urgency as accepted after a failed learned-policy probe | Focused tests plus 32k/probe evidence | Diagnostics are retained; opportunity penalty is documented and disabled as active default. | After E | 2 | pass, held outcome |
| `A4-SIG-G Closure` | main thread | n/a | Sync A3/M1/M2 decision and close residuals. | A4 README/status, parent air-combat README, M1/M2 docs | M2 release without A4 gate | Focused tests and docs check | Accepted/held status is evidence-backed. | Last, serial | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not let two workers edit the same reward table, scenario, routing contract,
  or status line concurrently.
- Keep short-evidence and closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  wave.
- Follow [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/hmoe/test_hmoe_routing.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/training/test_air_combat_active_training_entries.py
```

Optional short evidence run:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a4_authorized_first_shot_routed_retained_temporal_32k_20260603
```

## Acceptance Criteria

- New reward terms are zero by default and only affect configured scenarios.
- Reward tests show shaping is awarded in an authorized pre-release window and
  withheld after single-shot budget is consumed.
- The S1 C2/ROE active entry remains discoverable and does not mutate existing
  M1 `basic` baselines.
- Learned-policy evidence either demonstrates deterministic authorized first
  release or narrows the residual to binary pulse optimization.

## Residual Map

Immediate:

- Continue through
  [A5 constrained event-action modeling](../a5_constrained_event_action_model/README.md)
  rather than another reward-only pulse target.

Follow-on:

- Re-run learned-policy evidence only after A5 has explicit event action
  semantics and post-launch suppression.

Deferred:

- M2 release, sequence-native policy, self-play, and real-world shot doctrine.
