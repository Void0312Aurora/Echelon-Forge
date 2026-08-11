# Naval Domain Surface Split Task Clusters

Status: `2026-06-12`; `P1-A/P1-B/P2-A/P3-A/P3-B/P4-A` accepted; finite
task-cluster plan for [Naval Domain Surface Split](README.md).

Model IDs on accepted rows preserve the historical dispatch record. They are
not current selection guidance. Any planned or reopened cluster must choose a
current capability/risk tier, available model, and reasoning budget under the
[Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Boundary Decision

This subproject may modify naval task documentation, active naval training-entry
guards, command/action/observation adapters, and focused tests needed to move
maintained naval execution away from air-first compatibility carriers.

It must not claim N5 weapon engagement, N6 damage authority, fleet C2 maturity,
or learned-policy success. Shared runtime infrastructure may be reused only when
the policy-visible naval semantics are owned by common or naval surfaces, not by
air takeoff, runway, formation, gear, or flight-control fields.

## Finite Task Cluster List

| Cluster | Owner | Historical dispatch record / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | current | Create the subproject, status, queue, acceptance, and parent naval index links. | `docs/domains/naval/work/active/naval_domain_surface_split/**`, `docs/domains/naval/README*` | runtime code, tests, capability promotion | `git diff --check -- docs/domains/naval` | required files exist and parent README links the project | serial first cluster | 1 | pass |
| `P1-A` | worker `Linnaeus` | `gpt-5.4-mini` / `xhigh` | Inventory every air-first dependency still on the active naval policy/runtime path. | `naval_domain_surface_split_current_status_20260601*.md`, optional diagnostics notes | code changes, refactors | read-only `rg` inventory plus cited file/line evidence | inventory classifies each dependency as accepted shared, compatibility adapter, or blocker | after `P0-A`; read-only can run alone | 1 + 1 repair | accepted |
| `P1-B` | worker `Locke` | `gpt-5.4` / `high` | Add guard tests that prevent active naval entries from regressing to air action or air mission-observation surfaces. | `tests/training/**`, `tests/eval/**`, active naval config tests only | new packet implementation, N5 behavior | focused pytest for naval active entries and baseline eval | tests fail on `takeoff*`, air formation/takeoff mission modes, weapon/damage reward leakage | after `P1-A` dispatch; can precede implementation | 1 + 1 repair | accepted |
| `P2-A` | worker `Locke` | `gpt-5.4` / `high` | Design and implement a naval-owned action/intent assignment seam or explicit adapter around the current `PilotAction` carrier. | `src/runtime/contracts/**`, `gym_envs/universal_env_parts/**`, `python/rl/runtime/**`, focused tests | full helm/autopilot doctrine, weapon switches | C++/binding build if touched; focused world-batch naval tests | maintained naval path no longer treats `PilotAction` semantics as policy action truth | after accepted `P1-A/P1-B`; not parallel with `P2-B` | 2 + 1 repair | accepted |
| `P2-B` | future worker | n/a | Bound `MissionCommand` compatibility use behind shared-core and naval-owner projection tests. | `src/components/command/**`, `src/runtime/contracts/**`, `python/rl/profile/naval_profile.py`, command-chain tests | nested rewrite of all command consumers | command roundtrip tests, world-batch command-chain tests | naval station/ROE/assigned-target fields survive via maintained naval slices | after `P1-A`; not parallel with `P2-A` if same contract files | 2 + 1 repair | planned |
| `P3-A` | main thread | current | Promote `naval_screen_station_v1` toward a maintained naval observation packet. | `python/mission_obs_taxonomy.py`, `gym_envs/scenario_loader/mission_observation.py`, observation runtime/batching, tests | weapon/damage observation, fleet C2 schema | mission observation taxonomy and naval reward/observation tests | policy-visible naval vector is not an air takeoff/formation fallback | after `P2-A` boundary accepted | 2 + 1 repair | accepted |
| `P3-B` | worker `Linnaeus` | `gpt-5.4-mini` / `xhigh` | Add domain-neutral config aliases where air-labeled knobs block naval ownership. | `python/env_config.py`, `train.py`, examples config docs, tests | breaking existing air configs | env-config tests and naval training-entry bootstrap | naval entries can use neutral names while legacy air names remain compatible | after accepted `P1-B`; disjoint from `P2-A` write set | 1 + 1 repair | accepted |
| `P4-A` | main thread | current | Integrate active naval configs, eval gates, and contracts onto the accepted split surfaces. | `examples/config/training/active/naval/**`, `tools/eval/**`, `tests/runtime/naval/**`, `tests/eval/**` | formal training, N5/N6 release | naval active pytest, eval CLI smoke, scenario contracts | active entries run on new surfaces and still forbid airfield/weapon/damage terms | after `P2/P3` accepted | 1 + 1 repair | accepted |
| `P5-A` | main thread | current | Close or hold the subproject with acceptance and parent progress updates. | `docs/domains/naval/work/active/naval_domain_surface_split/**`, `docs/domains/naval/README*`, optional current progress update | late implementation | `git diff --check -- docs/domains/naval` plus recorded test outcomes | acceptance doc records pass/held residuals without overclaim | serial final cluster | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same normative table, public API,
  scenario contract, or status line concurrently.
- Keep command/action contract work serial when it touches
  `src/runtime/contracts/**`.
- Keep acceptance and parent README closure serial.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  wave.
- Follow [Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Worker packets must also state whether any remaining `PilotAction`,
`MissionCommand`, `flight_shaping`, runway, takeoff, formation, gear, or ILS
dependency is accepted shared infrastructure, a compatibility adapter, or a
blocker.

## Validation Plan

Baseline validation for documentation-only slices:

```bash
git diff --check -- docs/domains/naval
```

Focused runtime validation expected before implementation acceptance:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/training/test_naval_training_entry_contracts.py \
  tests/training/test_naval_training_entry_contracts.py \
  tests/eval/test_evaluation_cli_contracts.py \
  tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/runtime/naval/test_naval_station_policy_surface.py
```

Add narrower build, binding, or contract commands in the worker packet whenever
`src/`, `python/rl/runtime`, `gym_envs`, active configs, or scenario contracts are
touched.

## Acceptance Criteria

- Active maintained naval entries do not use air takeoff action or air
  formation/takeoff mission-observation semantics.
- A naval-owned action/intent path, or an explicitly bounded compatibility
  adapter, replaces policy-visible `PilotAction` truth for maintained naval
  entries.
- `MissionCommand` compatibility shell use is tested as a projection transport,
  not treated as the owner of naval semantics.
- Naval observation fields are named and tested as naval fields.
- Config aliases or wrappers stop exposing naval ownership as air
  `flight_shaping` behavior.
- N4 contracts stay green and N5/N6 claims stay blocked.

## Residual Map

Immediate:

- `P1-A/P1-B` completed the active air-first dependency inventory and
  regression guards;
- `P2-A` established the `naval_station_command` policy family and
  compatibility-only `PilotAction` transport adapter;
- `P3-B` moved active naval config to the domain-neutral `shaping_backend`
  alias;
- `P3-A` bounded `naval_screen_station_v1` as a maintained Python observation
  adapter with `basic` only as the compiled batch fallback;
- `P4-A` added active/eval `surface_gate` checks for the action command surface,
  legacy transport adapter, and naval observation adapter;
- the next dispatch should focus on `P2-B` command projection while still
  avoiding concurrent `src/runtime/contracts/**` write sets.

Follow-on:

- N5 launch/reject package after action/command ownership is accepted;
- formal training evidence after observation, reward, and eval gates mature.

Deferred:

- full helm/autopilot doctrine;
- high-fidelity damage and kill authority;
- fleet C2 or multi-ship learned tactics.
