# A5 Constrained Event Action Model Task Clusters

Status: `2026-06-03` finite task-cluster plan for
[README.md](README.md).

## Boundary Decision

A5 may change the S1 C2/ROE action contract, observation support fields, runtime
release state machine, policy event distribution, active probe configs,
diagnostics, tests, and task documentation needed to make missile release a
constrained event action. A5 must not modify missile physics, damage authority,
Pk/fuze authority, true BVR doctrine claims, M2 release, self-play, or `2v2`.

The selected long-range architecture is state machine + action mask + event
head. Masked categorical `hold/fire_once` is the preferred first implementation;
event Q-head is a planned follow-on if deterministic timing still needs value
comparison; hazard and option models are deferred until the event surface is
stable.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A5-EAM-A Boundary` | main thread | n/a | Create A5 scope, status, dispatch, acceptance, archive boundary, and parent links. | `docs/task/air_combat/a5_constrained_event_action_model/**`, parent air-combat README, A4 residual docs | Runtime or policy implementation | `git diff --check -- docs/task/air_combat` | Standard files exist and parent docs link A5. | first, serial | 1 | pass |
| `A5-EAM-B Surface Audit` | current-session subagent `Lagrange` | inherited model / xhigh, read-only audit | Map current action, observation, reward, policy, diagnostics, and config touchpoints. | A5 status docs, optional code-scan evidence under A5 | Changing runtime before contract freeze | read-only scan plus link check | Write-set and risk map are precise enough for implementation. | after A; can run before code edits | 1 + 1 repair | pass |
| `A5-EAM-C Event Contract` | main thread | high-reasoning design | Define `engagement_state`, `fire_mask`, event actions, allowed transitions, and deterministic evaluation semantics. | `docs/standards/air/act*.md`, A5 docs, focused contract tests as needed | Real-world doctrine, missile physics | markdown checks plus contract/unit tests | Contract separates legality from reward preference. | after B; serial with D/E table edits | 1 + 1 repair | pass, tests pending in D/E |
| `A5-EAM-D Runtime State Machine` | current-session subagent `Noether` | inherited model / high, implementation | Implement `AuthorizedReady -> FiredAssess` fire-once flow and post-launch fire suppression. | `gym_envs/**`, `scenarios/air_combat/1v1/**`, runtime tests | Policy distribution, reward-only fix | runtime and scenario tests | Accepted fire consumes event and suppresses repeat fire until explicit reattack state. | after C; parallel with E only through disjoint write set | 2 | pass |
| `A5-EAM-E Policy Event Head` | current-session subagent `Hume` | inherited model / high, implementation | Add masked event action semantics or event Q-head support with correct PPO log-prob/eval behavior. | `python/rl/policy_algo/**`, `python/rl/runtime/**`, HMoE/policy tests | Sequence-native M2 or option-critic | policy forward/evaluate tests, finite entropy/log-prob checks | Stochastic and deterministic paths share the same masked action support. | after C; parallel with D only through disjoint write set | 2 | pass |
| `A5-EAM-F Reward And Config Cleanup` | current-session subagent `Noether`, main-thread integration | inherited model / high, implementation | Move active S1 C2/ROE entries to event-action semantics and reduce invalid-fire penalty dependence. | `gym_envs/scenario_loader/reward_runtime/air_combat.py`, active config JSON, reward/config tests | Claiming learned policy success from config changes | reward/config tests | Constraints are mask/state-machine responsibilities; reward expresses outcomes and timing preferences. | after D/E minimal path | 2 | pass |
| `A5-EAM-G Diagnostics And Evidence` | current-session subagent `Hume`, main-thread integration | inherited model / high, implementation after read-only pre-audit | Extend probes to report event state, mask, requested/executed fire, post-launch suppression, and deterministic/stochastic outcomes. | `tools/diagnostics/**`, `python/training_callbacks.py`, A5 evidence docs, diagnostics tests | Staging `experiments_tmp`, accepting one lucky run | diagnostics tests plus focused probes | Evidence distinguishes structural multi-fire, invalid requests, and learned hold/fire behavior. | after D/E/F; closure evidence serial | 2 | pass |
| `A5-EAM-H Acceptance And Closure` | current-session subagent `Lagrange` pre-audit, main thread closure | inherited model / xhigh, read-only pre-audit before serial closure | Decide accepted or held, sync A3/A4/M1/M2 and parent README. | A5 README/status/acceptance, A4 README residuals, parent air-combat README, model docs if needed | M2 release without A5 gate | focused test suite, docs check, learned-policy evidence review | Accepted/held status is evidence-backed and overclaims remain refused. | last, serial | 1 | held closure pending cross-doc sync |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative action table, policy
  distribution, runtime state-machine contract, scenario config, or status line
  concurrently.
- No new conversation threads may be created. If subagents are available in the
  current session, use them only inside the write sets above.
- Keep boundary, acceptance, and closure clusters serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a
  follow-up wave.
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

Initial docs-only validation:

```bash
git diff --check -- docs/task/air_combat
```

Expected focused implementation validation, refined after `A5-EAM-B/C`:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/air_combat/test_air_combat_reward_surface.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_air_combat_process_probe.py
```

Learned-policy validation must record deterministic and stochastic probes and
must not stage `experiments_tmp`.

## Acceptance Criteria

- Accepted S1 C2/ROE policy-facing release uses constrained event semantics,
  not a raw per-frame continuous threshold or unconstrained Bernoulli.
- Illegal fire is removed from action support outside valid event states.
- Post-launch state suppresses repeat fire until explicit reattack permission is
  present.
- PPO log-prob, entropy/stats, stochastic sampling, and deterministic eval all
  respect the same event mask.
- Diagnostics can explain requested versus executed release and post-launch
  suppression.
- Learned evidence either demonstrates deterministic authorized first shot or
  records an explicit held residual outside reward-only tuning.

## Residual Map

Immediate:

- Freeze the event contract before runtime/policy edits.
- Fix HMoE residual gate load/eval consistency before relying on learned
  residual event behavior.

Follow-on:

- Event Q-head for value comparison if masked categorical still leaves unstable
  deterministic timing.
- Hazard / first-event timing model once valid windows and event datasets are
  stable.

Deferred:

- Hierarchical option / option-critic release flow.
- M2 sequence-native policy release.
- `2v2`, self-play, and real-world BVR doctrine claims.
