# Air EW Completion

Status: `2026-10-06` active; E1 local gates passed, stacked PR publication/review pending.

Document kind: plan
Lifecycle: active
Canonical: docs/domains/air/work/active/ew_completion/README.md
Owner: domains/air
Last verified: 2026-10-06

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)
- The task cluster file is an English-canonical implementation slice.

Inputs:

- [Air owner](../../../README.md)
- [EW entry review](../../../reviews/scripted_ew_entry_surface_20260925.md)
- [Pilot observation contract](../../../standards/pilot_observation_contract.md)
- [Closure policy](../../../../../engineering/automation/standards/wp_closure_lane_policy.md)

## Purpose

Complete the authorized Air EW work in dependency order, with finite acceptance
clusters and reviewable stacked PRs. Local mechanism acceptance is separate from
named-scenario playability and platform calibration.

## Current State

| Area | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Decoy seduction | merged | native `test_air_ew_decoy.cpp` | typed cell/FOV/discrimination model; calibration remains authored |
| Jamming | merged | native `test_air_ew_jamming.cpp`, PRs #99-#101 | target-attached binary noise denial and same-target DRFM range offset |
| RF/ESM data | E1 local pass | `test_air_ew_rf_contract.cpp` | explicit emission groups, receiver band/sensitivity/memory/confirmation |
| ESM observations | E1 local pass | `test_air_ew_esm.cpp`, Python Air adapter | no range/position solution, no canonical RL shape change |
| Temporal/cooperative/admission/terminal | queued | task cluster file | no promotion of Air capability or canonical modes |

## Scope

The ordered scope is passive ESM evidence, bounded jammer effects/resources,
temporal observation, cooperative command behavior, explicit action admission,
and named terminal acceptance. Real-platform EIRP/frequencies, emitter libraries,
antenna sidelobes, pulse processing, ghost tracks and calibrated J/S require
separate authored evidence and are not implied by this engineering model.

## Phase Plan

| Cluster | Goal | Entry | Exit | State |
| --- | --- | --- | --- | --- |
| E1 | RF/ESM contract and observation | merged jamming baseline | native negative cases, content validation, Python projection, state roundtrip | active |
| E2 | Jammer resources and effectiveness | E1 verified | bounded band/effect decision, cooldown/duty resource state and signed DRFM behavior with negative cases | queued |
| E3 | EW temporal history | E1/E2 verified | opt-in history state, reset/replay, compatible policy extraction | queued |
| E4 | Cooperative EW | E2/E3 verified | loss/latency, stale intent expiry, reassignment and role/resource isolation | queued |
| E5 | Canonical action admission | E3/E4 verified | explicit compatible mode registration and observation/action acceptance | queued |
| E6 | Named terminal gate | E1-E5 verified | seed matrix, terminal reasons, objectives, effect/resource receipts, replay and residual verdict | queued |

## Task Clusters

[Execution and acceptance plan](ew_completion_task_clusters_20261006.md).
Each cluster has an implementation pass and up to two evidence-driven repair
passes; additional scope requires a named follow-on cluster, not silent widening.

## Outputs And Evidence

### E1 RF semantics

- `Sensor.rf_eirp_watts`, `rf_frequency_mhz`, `rf_bandwidth_mhz` form an optional
  complete positive finite emission group. `Jammer` uses explicit EIRP/frequency
  plus its existing `bandwidth_mhz`; ERP is not silently converted to EIRP.
- Free-space received power uses [ITU-R P.525-5 equation (5)](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en),
  isotropic receive gain, and a 1 m distance floor. A band overlap is an admission
  gate, not a claim of spectrally integrated power. Current sensor Pd, LOS, FOV,
  weather and smooth-earth horizon gates remain engineering approximations.
- Omitted RF groups retain the legacy proxy; `require_rf_contract` rejects them.
  No concrete RF group is added to shipped equipment without evidence.
- Confidence is the fraction of required distinct observations before the
  evidence track expires. Each gap must be at most `memory_s`; this is not a
  sliding-window scan count, probability of detection or Bayesian identity confidence.
- Radar and jammer evidence remain separate internally and share the existing
  RWR source correlation. Explicit RF evidence takes precedence over a legacy
  proxy; among RF strobes, the greatest received dBm at the same time wins;
  newer weaker measurements replace stronger old measurements.
- An ordinary radar emission never asserts STT. The existing missile radar
  classifier is a coarse guidance-emitter proxy, not a radar mode machine or
  proof that a seeker is tracking the receiver.
- Coasting observations retain bearing, power and age until expiry; current
  lock/guidance flags are suppressed. `classify_emitters=false` hides public
  emitter classification. Clock rewind and world reset discard future evidence.
- RWR signal strength keeps its legacy proxy scale. Physical dBm and threshold
  margin are separate fields, avoiding a mix of mW and legacy scores.
- `AgentObservation.esm_detections` is a declared passive DTO. Its `source_id`
  preserves RWR source correlation; it supplies no position/range solution.
- `build_air_esm_matrix` exposes ten columns: bearing, dBm, RF-valid, margin, age,
  confirmation confidence, classification-known, jammer, lock, guidance. Source
  identity is omitted. `include_esm=True` opts in without altering default keys.

### Validation

Local E1 stack implementation validation, MSVC Release / Python 3.12:

- Built `ef_test`, `ef_py`, and `ef_runtime_host_candidate_test` after the last
  code change.
- Full `ef_test`: 255 cases, 155031 assertions passed.
- State-owner adapter suite: 16 cases, 484 assertions passed.
- Eight focused Python modules from the task-cluster recipe: 73 tests and 42
  subtests passed. After the final sensing/projection correction, the four
  affected facade/adapter/binding modules passed 44 tests and 32 subtests.
- Documentation governance/link tests: 23 passed, two pre-existing failures
  verified in `origin/main`: missing `Last verified:` in the architecture
  algorithm-substitution review and duplicate `systems/README` registry rows.
  The maintained link audit passes; the Air index hashes are refreshed.
- Independent base `1eb926689`: all three targets built; RF/legacy EW/content
  suites passed 43 cases and 1014 assertions; state-owner suite passed 16 cases
  and 484 assertions; content schema passed three tests and ten subtests.
- `git diff --check` passed. Remote checks/review remain publication gates.

## Acceptance Gate

E1 can be mergeable only after RF sensitivity/band/legacy/malformed negatives,
confirmation/expiry/reset, same-source mount selection, state reflection, native
EW regressions and Python adapter/content tests pass on the published tree.
The first PR defines content/state/passive DTO contracts; the second activates
the sensing model, DTO projection and optional Python adapter.
Publication/checks/review remain distinct gates. E6, not E1, owns playability.

## Residuals And Next Steps

- E2 owns external/support-jammer composition, frequency-sensitive radar denial,
  duty/cooldown budget and richer DRFM mechanics; current denial is attached to
  the sensed target and no ghost-track lifecycle exists.
- E3 owns history-enabled RL policy compatibility; E1 adds no canonical RL key.
- E4 owns formation and command delivery acceptance; existing 2v2 terminal
  surrogates do not establish these gates.
- E5 owns canonical action-mode admission; E6 owns named terminal acceptance.
- Historical sensor reflection included an absent `enforce_radar_horizon`
  member. E1 removes it, verifies current reflection, and normalizes the exact
  legacy inline/mounted sensor shape before strict import. Ambiguous mixed
  old/RF shapes are rejected; broad cross-revision state parity is not inferred.
- The coarse missile-emitter labels and free-space gain assumptions remain
  engineering semantics until a validated emitter library/model is authored.

## Archive

Keep this package active until the declared E1-E6 outcomes and residual owners
are recorded. Archive only after review, bilingual/index closure and an explicit
acceptance decision. PR creation alone does not close the package.
