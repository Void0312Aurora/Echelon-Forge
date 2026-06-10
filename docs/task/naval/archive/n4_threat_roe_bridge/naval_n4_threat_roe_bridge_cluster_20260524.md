# Naval N4 Threat / ROE Bridge Task Cluster

Status: `2026-05-25` accepted cluster for the first naval scenario expansion
after the DDG/T-AKE screen/contact MVP. Dispatch queue and acceptance records:
[N4 dispatch queue](naval_n4_threat_roe_dispatch_queue_20260524.md),
[N4 RL preflight](naval_n4_rl_task_surface_preflight_20260525.md), and
[N4 integration acceptance](naval_n4_integration_acceptance_20260525.md).

Cluster: `N4-0 Planning Surface`

Model / reasoning: `gpt-5.4`, medium

Round cap: one implementation round for this planning surface. If the cluster
cannot close in one round, return `partial` or `blocked` and re-scope before
adding more sidecar documents.

## Decision

The next naval scenario should be `ddg51_take1_screen_threat_roe_v1`.

This is an `N3 -> N4` bridge. It should extend the current DDG/T-AKE screen
and contact-report baseline by adding threat classification, ROE state, and
auditable target assignment. It should not require firing, hit assessment,
damage propagation, or combat termination.

Recommended release order:

1. `threat_roe_v1`: threat evaluation and ROE state, no mandatory firing.
2. `limited_engagement_v1`: one controlled weapon release after N4 gates pass.
3. `damage_outcome_v1`: damage and termination become scenario objectives only
   after N5 engagement evidence is stable.

## Realism Boundary

| Grade | Scenario capability | Release posture | Proof allowed | Proof forbidden |
|-------|---------------------|-----------------|---------------|-----------------|
| `N1-N3` | existing screen/contact MVP | accepted baseline | ship motion, station keeping, contact/report, shared-track, single DDG/HVU screen geometry | full fleet C2, fire-control realism, damage outcomes |
| `N4` | threatened maneuver and ROE | next bridge scenario | threat state, ROE state, target-assignment provenance, sensor quality affecting decision state | weapon release as required objective, hit/intercept proof, damage/kill proof |
| `N5` | limited weapon engagement | follow-on only | launch/reject event, valid track, range/arc/cooldown/inventory gates | damage outcome as primary proof |
| `N6` | damage and termination | deferred | mission/mobility/sensor kill proxy bound to outcome and reward | any `threat_roe_v1` proof |

Critical boundary: `threat_roe_v1` may make firing possible in the broader
runtime, but the scenario must not use successful firing or damage as its
acceptance proof. Unauthorized or unsupported firing should be treated as a
failed decision path, not as evidence that N5 is ready.

## Scenario Candidate

Candidate:

- `ddg51_take1_screen_threat_roe_v1`

Minimum scenario shape:

- blue `DDG-51` screens blue `T-AKE-1`;
- red surface contact approaches from outside the HVU blind-zone gate;
- DDG obtains and shares the track;
- HVU receives the shared track and report;
- threat state escalates only from a valid track with source/provenance;
- ROE state becomes observable and auditable;
- screen geometry remains within the accepted N3 station window;
- the scenario terminates before weapon release, or treats any release as an
  explicitly out-of-scope transition.

Expected N4 assertions:

- a contact cannot become an assigned threat without a valid track identity or
  track provenance;
- ROE state is derived from scenario conditions rather than hard-coded as a
  static metadata label;
- the task surface distinguishes `monitor`, `threatened`, and `authorized` or
  equivalent pre-fire states;
- N4 observations preserve enough state for RL preflight without claiming a
  trained policy.

## Finite Task Cluster List

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `N4-0 Planning Surface` | main thread | `gpt-5.4`, medium | Record the finite N4 bridge plan and distribution constraints. | `docs/task/naval/n4_threat_roe_bridge/**`, `docs/task/naval/README*.md` | scenarios, tests, runtime code, bindings, dispatch queues | `git diff --check -- docs/task/naval` | README and cluster docs record scenario decision, realism boundary, clusters, validation, gates, and residuals | current cluster; no dependency | 1 round | implemented |
| `N4-A Scenario / Contract Boundary` | future worker | `gpt-5.4`, high | Add the scenario fixture and scenario-level contract for N4 threat/ROE. | `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`; `tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json`; focused loader/contract test paths named in dispatch | weapon release, damage, RL rewards, runtime refactors | scenario contract runner for the new spec; existing naval screen contracts | new scenario loads, preserves N3 gates, and exposes N4 threat/ROE assertions without N5/N6 claims | dependency-gated by `N4-0`; can run before `N4-B`; downstream clusters depend on its accepted boundary | 2 rounds | pass / accepted |
| `N4-B Threat / ROE Semantics` | future worker | `gpt-5.4`, high | Implement or bind maintained threat-state, ROE-state, and target-assignment provenance needed by the scenario. | narrowed dispatch packet required before work; expected families are naval tasking/profile, mission command, and focused tests | weapon effects, damage model, broad command-chain rewrites | focused runtime/leader tests plus existing naval mission-command tests | no fire without authorization; assigned target comes from a valid track; state is exposed through maintained contracts | depends on `N4-A`; may run in parallel with `N4-C` only if write scopes are disjoint | 2 rounds | pass / accepted |
| `N4-C Runtime / Facade Evidence` | future worker | `gpt-5.4`, high | Prove N4 fields travel through maintained facade/world-batch surfaces rather than raw whole-shell rollback paths. | narrowed dispatch packet required before work; expected families are world-batch command-chain cache, vec-env tests, and facade guards | new scenario geometry, reward design, weapon behavior | world-batch naval command-chain tests; facade/architecture guards if touched | N4 fields survive batch sync and export through maintained assignments | depends on `N4-A`; parallel-safe with `N4-B` only after write scopes are checked | 2 rounds | pass / accepted |
| `N4-D RL Task Surface Preflight` | main thread | `gpt-5.4`, medium | Sketch observation/action/reward/termination for a later `naval_contact_report` or `naval_screen_station_hold` curriculum using the N4 state. | `docs/task/naval/n4_threat_roe_bridge/naval_n4_rl_task_surface_preflight_20260525*.md` | learned policy claims, trainer launch, reward tuning by experiment | `git diff --check -- docs/task/naval` | RL surface names N4 signals and termination rules while refusing N5/N6 claims | consumes accepted `N4-A/B/C`; no further dispatch in this wave | 1 round | pass / accepted |
| `N4-E Integration / Acceptance` | main thread | `gpt-5.4`, high | Collect evidence, synchronize README/current-progress status, and decide whether to open N5 limited engagement. | `docs/task/naval/**` acceptance/status files explicitly named at dispatch | implementation changes, late feature additions | full command set recorded by completed workers; `git diff --check -- docs/task/naval` | all prior clusters returned complete packets; residuals and next gates are recorded | serial after `N4-A` through `N4-D` | 1 round | pass / accepted; N5 blocked |

## Dispatch Rules

Implementation dispatch now runs through
[N4 dispatch queue](naval_n4_threat_roe_dispatch_queue_20260524.md). Every
worker packet must map to one stream in the finite cluster list above and follow
the authoritative
[Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

Required worker result shape:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Additional constraints:

- do not split the same scenario contract or normative threat/ROE table across
  concurrent workers;
- keep `N4-E Integration / Acceptance` serial until implementation clusters
  return complete packets;
- if a cluster exceeds its round cap, re-baseline the cluster before assigning
  more follow-up work;
- if runtime work requires paths outside the planned write set, stop and
  narrow the dispatch packet before editing.

## RL Preflight Surface

Observation candidates:

- ownship-to-HVU station error;
- ownship speed/heading and relative bearing to the contact;
- contact range, bearing, closure rate, track source, and confidence;
- HVU blind-zone exposure flag;
- threat state, ROE state, assigned-target id/provenance;
- latest report and command-chain status.

Action candidates:

- keep current screen station;
- adjust station offset or speed command within N3 limits;
- report or classify contact;
- request or acknowledge ROE state;
- explicitly no weapon-release action in `threat_roe_v1`.

Reward candidates:

- maintain screen geometry;
- keep the HVU protected while preserving shared-track/report behavior;
- reward timely and justified threat-state transition;
- penalize false escalation, stale track use, station loss, or unauthorized
  firing attempts.

Termination candidates:

- contact exits the threat window after correct handling;
- HVU is exposed beyond accepted N3 tolerance;
- threat/ROE state cannot be justified by valid track provenance;
- timeout;
- any required N5/N6 behavior is encountered before the bridge scenario is
  explicitly promoted.

## Validation Plan

Docs-only validation for this cluster:

```bash
git diff --check -- docs/task/naval
```

Expected implementation validation after `N4-A`:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_contact_report_geometry.json
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/naval/naval_screen_closing_contact_geometry.json
```

Expected regression surface if runtime/facade code is touched:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/naval/test_naval_screen_scenario.py tests/leader/test_tasking_profile_contracts.py tests/leader/test_command_field_projection_contracts.py
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "naval or task_order or command_chain"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "naval_owner_slice or task_order_naval or command_chain"
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py tests/runtime/mission/test_naval_mission_command_mapping.py tests/runtime/mission/test_ship_mission_command_authority.py
```

## Acceptance Criteria

The N4 bridge is not accepted until:

- the scenario and contract prove N3 baseline behavior still holds;
- threat state has a valid track source and provenance;
- ROE state is observable in maintained contracts or facade projections;
- target assignment cannot appear from static metadata alone;
- unauthorized firing is rejected, ignored, or recorded as out-of-scope;
- the docs continue to label the scenario as `N4`, not `N5` or `N6`;
- RL material remains a preflight surface unless a later training/eval package
  exists and passes.

## Residual Map

Immediate:

- keep `ddg51_take1_screen_threat_roe_v1` accepted as a pre-fire N4 bridge;
- use the RL preflight as the next implementation spec only after owner
  approval.

Follow-on:

- `limited_engagement_v1` can open only as an N5 package with launch/reject,
  range/arc/cooldown/inventory, and non-damage gates.

Deferred:

- hit/intercept evidence;
- damage propagation and damage-bound termination;
- fleet C2, ASW, embarked air, and UNREP realism beyond existing MVP surfaces.
