# A3 C2/ROE Release Discipline Task Clusters

Status: `2026-06-03` A-H pass task-cluster record for
[README.md](README.md).

Chinese companion:
[a3_c2_roe_release_discipline_task_clusters_20260602.zh.md](a3_c2_roe_release_discipline_task_clusters_20260602.zh.md)

## Boundary Decision

A3 may add an air-combat C2/ROE contract, observation surface, reward/diagnostic
terms, and S1 probe entries. It may not claim classified ROE, real BVR shot
doctrine, Pk authority, missile physics authority, or sequence-native policy
release. Repeated launch must be classified against an explicit command state
before it is used as M2 evidence.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A3-ROE-A Source And Boundary` | main thread or read-only diagnostics worker | n/a | Record public C2/ROE terms and non-claims. | `docs/task/air_combat/a3_c2_roe_release_discipline/*source*`, README source sections | Classified tactics, exact shot doctrine, copied manuals | Link/source review, `git diff --check` | Source scan links stable sources and records boundaries. | Parallel with B; serial before C. | 1 | pass |
| `A3-ROE-B Code Surface Audit` | read-only diagnostics worker | n/a | Map existing mission command, observation, reward, scenario, config, and diagnostic surfaces. | A3 docs only | Code edits, implementation design beyond cut-in map | File/line review, `rg` audit | Cut-in table lists files, tests, and residuals. | Parallel with A; serial before C/D/E. | 1 | pass |
| `A3-ROE-C Schema Contract` | main thread | n/a | Define `air_combat_c2_roe_v1` fields, value ranges, state transitions, and fail-closed defaults. | A3 README/task docs, `python/mission_obs_taxonomy.py` | Runtime C2 hierarchy, datalink, full air-defense model | Documentation review, field-list consistency check | Contract can distinguish hold, tight/free, engage, cease/abort, shot policy, and pending assessment. | Depends on A/B. | 2 | pass |
| `A3-ROE-D Observation Wiring` | integration worker | n/a | Expose the contract to policy observations. | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, observation/space tests | PPO/model rewrites, hidden reward-only state | Focused mission-observation field and shape tests | `mission_obs_mode=air_combat_c2_roe_v1` returns stable fields in single-env and world-batch paths. | Depends on C; can run before E if contract frozen. | 2 | pass |
| `A3-ROE-E Reward And Diagnostics` | integration worker | n/a | Add reward/diagnostic terms for ROE hold, unauthorized fire, authorized first shot, premature second shot, salvo, and reattack. | `gym_envs/scenario_loader/reward_runtime/air_combat.py`, diagnostics/probe files, focused tests | Silent fire suppression as the primary fix, missile physics changes | Reward unit tests, process-probe metric checks | Metrics split repeated launch into authorized and violation categories. | Depends on C; parallel with D after contract. | 2 | pass |
| `A3-ROE-F Scenario Config Probe` | worker | n/a | Add S1 C2/ROE probe scenario/config entries. | `scenarios/air_combat/1v1/**`, `examples/config/training/active/air_combat/**`, training-entry tests | Stage-2/3 tactics, self-play, red-weapons expansion | Bootstrap tests and short deterministic probe | Probe runs and emits expected C2/ROE metrics. | Depends on D/E. | 2 | pass |
| `A3-ROE-G M1 Evidence Review` | main thread | n/a | Reinterpret M1 repeated-launch evidence after A3 observability. | `docs/task/model/m1_temporal_window_hmoe/**`, optional A3 evidence doc | M2 implementation | Compare reactive/temporal probe metrics | M2 remains held or gets a justified release vote based on A3-aware evidence. | Depends on F/P4 evidence. | 1 | pass |
| `A3-ROE-H Closure And Index Sync` | main thread | n/a | Sync parent README, residuals, archive pointers, and acceptance state. | `docs/task/air_combat/README*`, A3 README/status docs, related model README | New feature scope | `git diff --check` and doc link review | Status lines and residual map agree across maintained docs. | Serial final cluster. | 1 | pass |

Current A-F note: A is `pass` because the public-source scan records terminology
and non-claim boundaries. B is `pass` because the code-surface scan maps mission
command, observation, reward, scenario, config, and process-probe cut-in points.
C is `pass` because the field order, values, and fail-closed defaults are
documented and registered. D is `pass` because the taxonomy, CLI,
single-env loader observation path, and `WorldBatchVecEnv.reset()` mission slot
all expose stable `air_combat_c2_roe_v1` fields. E is `pass` because additive
reward and process-probe buckets split authorized release, unauthorized/violation
release, pending assessment, shot budget, hold-fire, salvo, reattack, and legacy
fallback cases. F is `pass` because the S1 C2/ROE scenario/config pair boots,
keeps legacy M1 baselines on `basic`, enables the C2/ROE reward gate, and a short
process probe emitted authorized C2/ROE release metrics.

Current G note: G is `pass` because P4 process probes record both an authorized
single release (`forced_fire`) and repeated violation releases (`switch_explore`)
under the same S1 C2/ROE contract. M2 remains held because this is not a learned
temporal-policy acceptance.

Current H note: H is `pass` because the parent air-combat README, A3 README,
task clusters, M1 current-status docs, and M1 temporal entry now agree that the
bounded A3 C2/ROE layer is accepted while M2 remains held pending learned-policy
training/evaluation evidence.

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same mission-observation contract,
  ROE value table, training config pair, or status line concurrently.
- Source and code scans may run in parallel, but contract and implementation
  work must wait for their acceptance.
- Keep acceptance, M1/M2 interpretation, and parent-index sync serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a new wave.
- Follow the repository subagent usage policy; do not create new Codex
  conversation threads.

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

Latest local validation:

```powershell
git diff --check -- docs/task/air_combat docs/task/model
.\tools\maintenance\cmo_env.ps1 validate-rl
.\tools\maintenance\cmo_env.ps1 python -m pytest -q `
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py `
  tests/runtime/air_combat/test_air_combat_reward_surface.py `
  tests/runtime/core/test_env_config.py `
  tests/runtime/mission/test_mission_obs_taxonomy.py `
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py `
  tests/training/test_air_combat_training_entry_contracts.py `
  tests/world_batch/test_world_batch_vec_env.py::WorldBatchVecEnvTests::test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation
.\tools\maintenance\cmo_env.ps1 python train.py `
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json `
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json `
  --test_only
# Bootstrapped through mission_obs_mode=air_combat_c2_roe_v1; stopped at expected
# --test_only requires --resume_path boundary.
```

## Acceptance Standards

- A3 never treats public terms as classified tactics or calibrated real-world
  shot doctrine.
- The policy can observe the command state required to make fire/no-fire
  decisions.
- Repeated launch evidence separates authorized salvo/reattack from premature
  second-shot or unauthorized fire.
- M1/M2 decisions cite A3-aware metrics instead of raw missile count alone.

## Residual Map

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Self-defense override | future air-combat C2 expansion | S1 single-aircraft contract accepted and threat/self-defense tests defined. |
| Leader/wingman delegation | future multi-aircraft task | A3 single-aircraft command semantics stable. |
| Datalink/offboard sensing | future sensor/C2 task | Contact provenance and assigned-target source semantics are maintained. |
| Full no-fire/friendly logic | future ROE safety task | Friendly track identity and no-fire zones have runtime facts and tests. |
| M2 sequence-native policy | model workline | A3-aware evidence still shows memory/sequence gap after command constraints. |
