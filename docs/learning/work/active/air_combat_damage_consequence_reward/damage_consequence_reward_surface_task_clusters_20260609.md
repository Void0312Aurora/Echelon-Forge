# A2 Damage Consequence Reward Surface Task Clusters

Status: `2026-06-11` finite task-cluster plan for
[README.md](README.md). DCR-A-D are validated; DCR-E probe export,
diagnostics-only bridge, and read-only re-scope are validated, but fixed-fire
DCR totals remain zero. Controlled nonzero consequence-chain evidence is still
the next non-training gate; DCR-F remains planned.

Chinese companion:
[damage_consequence_reward_surface_task_clusters_20260609.zh.md](damage_consequence_reward_surface_task_clusters_20260609.zh.md)

## Boundary Decision

This follow-on may add configurable training rewards that consume already
observable damage consequences: damage reports, aircraft damage debug state, and
ground-contact lifecycle state. It may not change weapon effects authority,
invent real Pk, claim stock AIM-120C / MQ-9 lethality, or replace the damage
chain with a direct crash rule.

The first implementation slice should reward deltas and transitions, not the
static presence of a damaged target. That keeps delayed fire, fuel leak, control
loss, and severe impact useful as training feedback without paying the policy
again forever for the same consequence.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DCR-A Boundary And Observable Map` | main thread | n/a | Promote the held idea into an active A2 follow-on and list observable consequence sources. | `docs/learning/work/active/air_combat_damage_consequence_reward/**`, A2 pointer README if needed | Standard-doc rewrite, A9 creation, reopening sealed A2 archive | `git diff --check -- docs/learning/work/active/air_combat_damage_consequence_reward` | README and task-cluster plan exist with explicit forbidden claims. | first, serial | 1 | pass |
| `DCR-B Runtime Reward Surface` | main thread | n/a | Add optional reward terms for aircraft damage deltas and severe ground-contact transitions. | `gym_envs/scenario_loader/reward_runtime/air_combat.py` | Weapon physics changes, direct crash substitute, always-on training behavior shift without config | Focused reward unit tests | Runtime reads consequence state once per step and emits named terms only when configured/enabled. | after A | 2 | pass |
| `DCR-C Focused Tests` | main thread | n/a | Cover target reward, self penalty, once/delta semantics, and safe ground-contact boundary. | `tests/runtime/air_combat/test_air_combat_reward_surface.py`, optional focused 1v1 fixture tests | Slow training run, broad scenario rewrite | `python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py` | Tests prove the reward layer consumes facts without changing physical authority. | after or with B | 2 | pass |
| `DCR-D Scenario Opt-In` | current-session worker | n/a | Make Stage-2 able to consume low-weight consequence terms later. | `scenarios/air_combat/1v1/**`, `examples/config/training/active/air_combat/**`, active-entry README | Making Stage-2 training a kill-chain prerequisite, changing launch/firing closure, speed optimization, Stage-3/self-play | Scenario/config smoke or JSON check | Opt-in is explicit and term weights are documented as training synthetic. | after B/C | 1 | pass |
| `DCR-E Probe Evidence` | read-only diagnostics explorer, then diagnostics worker | n/a | Prepare and run a controlled hit/fixed-release/replay probe that reports launch terms and consequence terms separately. | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`, focused diagnostics tests, later diagnostics output docs under this subproject | Acceptance from one lucky seed, hiding no-effect shots behind release rewards, waiting on learned Stage-2 model as a prerequisite | Controlled probe or replay summary | Evidence shows whether consequence rewards appear after effects/damage, not just after release. | after D | 1 | partial: export/bridge/re-scope ready; `DCR-E-P3` fixture evidence next |
| `DCR-F Closure And Index Sync` | main thread | n/a | Mark the accepted slice or residuals and sync parent pointers. | This package, `docs/learning/README*`, and `docs/domains/air/README*` | Overclaiming real lethality or final Stage-2 acceptance | docs diff check and focused tests | Status lines and residual map match evidence. | last, serial | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow parallel writes to reward runtime, scenario reward weights, or
  status lines.
- A/B/C can happen in one main-thread slice because B is intentionally narrow.
- D/E/F must remain separate from any future multi-world speed work.
- Do not create a new Codex conversation thread; subagents, if used, must stay
  within the current session and the cluster write set.
- Current dispatch queue:
  [damage_consequence_reward_surface_dispatch_queue_20260609.md](damage_consequence_reward_surface_dispatch_queue_20260609.md)

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

Focused validation for the first slice:

```bash
git diff --check -- \
  docs/learning/work/active/air_combat_damage_consequence_reward \
  gym_envs/scenario_loader/reward_runtime/air_combat.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py
```

Latest local validation:

```bash
python -m py_compile gym_envs/scenario_loader/reward_runtime/air_combat.py tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_reward_surface.py
python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once \
  tests/runtime/air_combat/test_air_combat_1v1_fixture.py::AirCombat1v1FixtureTests::test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win
python -m py_compile tools/diagnostics/air_combat_weapon_employment_process_probe.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py
python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
python -m json.tool scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json >/dev/null
git diff --check -- \
  docs/learning/work/active/air_combat_damage_consequence_reward \
  gym_envs/scenario_loader/reward_runtime/air_combat.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  examples/config/training/active/air_combat/README.md \
  examples/config/training/active/air_combat/README.zh.md
```

`train.py --test_only` reached runtime preflight for Stage-2. A later 2 episode
x 512 step model-mode probe using
`experiments_tmp/a1_stage2_c2_roe_m3s2_initfrom_stage1_8k_20260608_r1/final_model.zip`
produced no release, no effects/damage, and 0 DCR reward. It proves the
probe/export path can run, not that consequence reward occurs after damage.
DCR-E should next use a controlled hit/fixed-release/replay artifact.

Later learned-policy probe validation, after controlled chain evidence exists:

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --test_only
```

## Acceptance Standards

- Reward terms are named by consequence type and remain separable from release
  rewards.
- Target damage consequences can add reward; self damage consequences can add
  penalty.
- Static damage presence is not repeatedly rewarded by default.
- Ordinary safe ground contact is not rewarded as a combat consequence; severe
  impact, gear collapse, or crashed-wreck transition can be rewarded if
  configured.
- The subproject continues to reject Pk, deterministic fuze, stock
  weapon-outcome, and special target-kill authority claims.

## Residual Map

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Stage-2 consequence signal may remain sparse | Future training consumer | Controlled chain evidence is already available; later learned-policy probe reports effects/damage/consequence terms after learned release. |
| Controlled kill-chain consequence evidence missing | DCR-E | A fixed-hit, fixed-release, or replay probe records effects/damage and nonzero DCR term timing together. |
| Fixed-fire bridge has zero DCR totals | DCR-E follow-up | `DCR-E-P3` controlled fixture produces DCR-readable consequence fields, or reward mapping from damage-report projections is separately scoped. |
| Reward weights are synthetic training knobs | DCR-D/F | Docs and configs label them as training shaping, not weapon truth. |
| Delayed fire/fuel dynamics may be too weak | Future A2 calibration | A separate fidelity/calibration task changes physical consequence strength. |
| Throughput may limit evidence collection | Future performance task | Multi-world or equivalent speed work is scoped outside this reward subproject. |
