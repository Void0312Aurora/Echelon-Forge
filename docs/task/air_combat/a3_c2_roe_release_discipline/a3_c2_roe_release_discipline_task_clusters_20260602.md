# A3 C2/ROE Release Discipline Task Clusters

Status: `2026-06-02` finite task-cluster plan for
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
| `A3-ROE-A Source And Boundary` | main thread or read-only diagnostics worker | n/a | Record public C2/ROE terms and non-claims. | `docs/task/air_combat/a3_c2_roe_release_discipline/*source*`, README source sections | Classified tactics, exact shot doctrine, copied manuals | Link/source review, `git diff --check` | Source scan links stable sources and records boundaries. | Parallel with B; serial before C. | 1 | active |
| `A3-ROE-B Code Surface Audit` | read-only diagnostics worker | n/a | Map existing mission command, observation, reward, scenario, config, and diagnostic surfaces. | A3 docs only | Code edits, implementation design beyond cut-in map | File/line review, `rg` audit | Cut-in table lists files, tests, and residuals. | Parallel with A; serial before C/D/E. | 1 | active |
| `A3-ROE-C Schema Contract` | main thread | n/a | Define `air_combat_c2_roe_v1` fields, value ranges, state transitions, and fail-closed defaults. | A3 README/task docs; later `python/mission_obs_taxonomy.py` if implementation starts | Runtime C2 hierarchy, datalink, full air-defense model | Documentation review, field-list consistency check | Contract can distinguish hold, tight/free, engage, cease/abort, shot policy, and pending assessment. | Depends on A/B. | 2 | planned |
| `A3-ROE-D Observation Wiring` | integration worker | n/a | Expose the contract to policy observations. | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, observation/space tests | PPO/model rewrites, hidden reward-only state | Focused mission-observation field and shape tests | `mission_obs_mode=air_combat_c2_roe_v1` returns stable fields in single-env and world-batch paths. | Depends on C; can run before E if contract frozen. | 2 | planned |
| `A3-ROE-E Reward And Diagnostics` | integration worker | n/a | Add reward/diagnostic terms for ROE hold, unauthorized fire, authorized first shot, premature second shot, salvo, and reattack. | `gym_envs/scenario_loader/reward_runtime/air_combat.py`, diagnostics/probe files, focused tests | Silent fire suppression as the primary fix, missile physics changes | Reward unit tests, process-probe metric checks | Metrics split repeated launch into authorized and violation categories. | Depends on C; parallel with D after contract. | 2 | planned |
| `A3-ROE-F Scenario Config Probe` | worker | n/a | Add S1 C2/ROE probe scenario/config entries. | `scenarios/air_combat/1v1/**`, `examples/config/training/active/air_combat/**`, training-entry tests | Stage-2/3 tactics, self-play, red-weapons expansion | Bootstrap tests and short deterministic probe | Probe runs and emits expected C2/ROE metrics. | Depends on D/E. | 2 | planned |
| `A3-ROE-G M1 Evidence Review` | main thread | n/a | Reinterpret M1 repeated-launch evidence after A3 observability. | `docs/task/model/m1_temporal_window_hmoe/**`, optional A3 evidence doc | M2 implementation | Compare reactive/temporal probe metrics | M2 remains held or gets a justified release vote based on A3-aware evidence. | Depends on F/P4 evidence. | 1 | planned |
| `A3-ROE-H Closure And Index Sync` | main thread | n/a | Sync parent README, residuals, archive pointers, and acceptance state. | `docs/task/air_combat/README*`, A3 README/status docs, related model README | New feature scope | `git diff --check` and doc link review | Status lines and residual map agree across maintained docs. | Serial final cluster. | 1 | planned |

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

Initial documentation validation:

```bash
git diff --check -- docs/task/air_combat docs/task/model
```

Expected future implementation validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest -q \
  tests/runtime/mission/test_mission_command_roe_fields.py \
  tests/runtime/air_combat/test_weapon_roe_runtime.py \
  tests/training/test_air_combat_active_training_entries.py
```

Additional A3 tests should be added for
`mission_obs_mode=air_combat_c2_roe_v1` and the S1 C2/ROE process-probe
metrics once implementation starts.

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
