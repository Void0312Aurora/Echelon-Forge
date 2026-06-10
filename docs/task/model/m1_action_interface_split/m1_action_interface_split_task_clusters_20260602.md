# M1 Action Interface Split Task Clusters

Status: `2026-06-02` finite task-cluster plan and implementation checkpoint for
[M1 Air-Combat Action Interface Split](README.md).

## Boundary Decision

This subproject fixes the training action interface, not missile release
physics. Existing runtime gates may remain as physical and command-contract
checks, but they must not be used as a hidden tactical-memory substitute.

The implementation may use a flat numeric transport vector for compatibility
with SB3 rollout buffers, but acceptance requires explicit hybrid semantics for
combat commands: continuous flight axes, Bernoulli-style switches, categorical
selectors and pulse release commands must be represented and tested as distinct
policy/action-adapter concepts.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M1-AS-A Evidence And Boundary` | main thread | current main thread | Record why `full` continuous switch dimensions are training-hostile while runtime release gates are still valid. | `docs/task/model/m1_action_interface_split/**`, `docs/task/model/README*` | code implementation, M2 release, missile kernel changes | `git diff --check -- docs/task/model` | README and cluster docs link parent model entry and refuse overclaims | serial first | 1 + 1 repair | pass |
| `M1-AS-B Action Contract Design` | main thread or future integration worker | high-reasoning design | Define the accepted air-combat action surface, including field names, reset behavior, held behavior, selector ranges, pulse duration and `proprio` semantics. | `docs/standards/air/act.md`, `docs/standards/air/act.zh.md`, `gym_envs/universal_env_parts/spaces.py`, `gym_envs/universal_env_parts/actions.py`, focused tests | tactical memory, damage, missile envelope changes | env-config tests, action adapter unit tests, markdown diff check | contract names a stable mode and all switch/pulse semantics | after `M1-AS-A`; serial with implementation touching same action tables | 1 + 1 repair | pass |
| `M1-AS-C Transition Adapter Probe` | main thread | implementation | Add a Box-compatible action-mode adapter path for pulse/effective-action behavior. | `gym_envs/universal_env_parts/actions.py`, `gym_envs/universal_env.py`, `python/rl/runtime/world_batch_vec_env.py`, active air-combat probe config, runtime tests | Gym Dict action-space migration, missile release kernel changes | action adapter tests, world-batch action/proprio tests, training bootstrap test | held `fire_weapon` policy command produces only a rising-edge one-frame release intent; effective action is visible in `proprio` | after `M1-AS-B` | 1 + 1 repair | pass |
| `M1-AS-D Hybrid HMoE Action Distribution` | main thread | high-reasoning implementation | Implement policy-side mixed action semantics for continuous flight axes plus discrete switches/selectors/pulse commands, while preserving PPO log-prob correctness. | `python/rl/policy_algo/policies.py`, HMoE tests | sequence-native PPO, recurrent hidden state, M2 Causal Transformer implementation | HMoE forward/evaluate tests, PPO smoke, non-finite probe | joint log-prob, deterministic mode and action shape are tested; entropy uses sampled fallback | after `M1-AS-B` | 1 + 1 repair | pass |
| `M1-AS-E Runtime Surface Wiring` | main thread | implementation | Wire the accepted action surface through `UniversalEnv`, `WorldBatchVecEnv`, temporal history and compiled observation bridge. | `gym_envs/universal_env.py`, `python/rl/runtime/world_batch/state.py`, `python/rl/runtime/world_batch_vec_env.py`, world-batch tests | naval action modes, cooperative weapon release, missile release kernel | world-batch temporal/action/proprio tests, single-env compatibility tests | reset/done/terminal observation and last-action history agree across maintained paths | after `M1-AS-B`; with `M1-AS-D` | 1 + 1 repair | pass |
| `M1-AS-F Active Probe Migration` | main thread | implementation | Add stage-1 active air-combat configs using the new action interface and pair them with `full` baselines. | `examples/config/training/active/air_combat/**`, `tests/training/test_air_combat_training_entry_contracts.py`, docs under this subproject | learned-policy acceptance, long training claim | training-entry pytest, `train.py --test_only` bootstrap, short smoke if implementation available | configs pair with same scenario, seed rules and temporal/reactive extractor settings | after runtime path passes | 1 + 1 repair | pass |
| `M1-AS-G Diagnostics And Acceptance` | main thread integration | evidence review | Record evidence on action reachability, launch attempts, invalid fire attempts, repeated launch interval and interaction with M1 temporal history. | `tools/diagnostics/**`, `docs/task/model/m1_action_interface_split/**`, M1 evidence docs | M2 implementation, tactical memory board, broad air-combat maturity claim | focused diagnostics, `git diff --check`, linked test results | acceptance or held residuals are documented and parent README remains synchronized | after `M1-AS-F`; closure serial | 1 review + 1 repair | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative action table, policy
  distribution, training config pair or status line concurrently.
- Keep `M1-AS-A` and `M1-AS-G` serial.
- Do not create new conversation threads for this project. If worker delegation
  is available in the current environment, it must follow the repository
  subagent policy and the cluster write sets above.
- If a cluster exceeds its round cap, stop and re-scope before adding a follow-up
  wave.

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
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/core/test_env_config.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "action or temporal_history"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/training/test_air_combat_training_entry_contracts.py
git diff --check -- docs/task/model docs/standards/air gym_envs python examples/config/training/active/air_combat tests tools
```

Narrower clusters may run smaller focused subsets, but acceptance must record
which commands were run and which were intentionally deferred.

## 2026-06-02 Worker Packet Summary

```md
status: pass
touched files:
  gym_envs/universal_env_parts/spaces.py
  gym_envs/universal_env_parts/actions.py
  gym_envs/universal_env.py
  python/env_config.py
  python/rl/policy_algo/policies.py
  python/rl/runtime/world_batch/state.py
  python/rl/runtime/world_batch_vec_env.py
  train.py
  examples/config/training/active/air_combat/**
  tests/runtime/core/test_air_combat_hybrid_action.py
  tests/policy/test_execution_policy_surface.py
  tests/policy/test_auxiliary_training_updates.py
  tests/training/test_air_combat_training_entry_contracts.py
commands/outcomes:
  python -m py_compile ...: pass
  pytest focused hybrid/runtime/HMoE/training entries: 40 passed
  pytest expanded bootstrap + hybrid/runtime/HMoE/training entries: 46 passed
  git diff --check scoped paths: pass
  32-step hybrid smoke train: pass
  1000-step hybrid load/predict/step smoke: pass
  Stage-1 hybrid range-gate action metrics: pass, release_count=1, invalid_fire_attempt_count=0
  Stage-1 full range-gate baseline: pass, same first_fire/release=1233
remaining paths:
  learned policy still needs shaping/curriculum before weapon-employment acceptance
behavior risks:
  entropy uses sampled fallback because squashed continuous axes have no closed form
  cooperative world-batch path is not part of the active air-combat config route
integration notes:
  no missile physics, damage, ammo, cooldown or tactical memory board changed
```

## Acceptance Criteria

- The accepted air-combat training action surface no longer relies on a raw
  continuous `fire_weapon > 0.5` threshold as the policy-facing command.
- Switch and selector commands have explicit reset, hold and repeat semantics.
- `proprio` / `proprio_history` semantics are defined for policy intent and
  effective transport action.
- PPO log-prob and entropy remain correct for any hybrid policy implementation.
- Stage-0 / Stage-1 probe configs can compare the new action surface against the
  old `full` surface without changing missile physics, damage or scenario truth.

## Residual Map

Immediate:

- Fold the action-interface acceptance into the M1-A4 / M1-A5 evidence review,
  while keeping M2 release held.
- Follow-on S1 training should prefer the hybrid action interface and add
  weapon-employment shaping/curriculum.

Follow-on:

- Fold successful action-interface evidence back into M1-A4 / M1-A5 release
  review before deciding on M2.
- Add target-engagement memory only after the action surface is stable and the
  policy can express intentional pulses.

Deferred:

- Sequence-native Causal Transformer PPO.
- Full cockpit HOTAS modeling.
- Missile model, damage model or tactical release-kernel changes.
