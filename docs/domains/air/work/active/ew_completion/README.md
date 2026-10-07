# Air EW Completion

Status: `2026-10-07` active; E1-E4 local mechanism gates pass. PRs #103-#107 have green normal checks; reviews are pending, and #104's CUDA toolchain job timed out during provisioning. E4-B awaits publication.

Document kind: plan
Lifecycle: active
Canonical: docs/domains/air/work/active/ew_completion/README.md
Owner: domains/air
Last verified: 2026-10-07

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
| Jammer resources/effect | E2 local pass | `test_air_ew_jamming.cpp`, jammer schema and state-owner suite | RF overlap gating, burst/cooldown receipts, signed same-target DRFM range offset |
| EW temporal history/policy | E3 local pass | `test_air_ew_temporal.py`, `TemporalTransformerExtractor` | opt-in EW history, valid-frame mask, reset/replay and policy checkpoint roundtrip |
| Shared command delivery | E4-A local pass | common scripted link and Joint compatibility/lifecycle tests | transport capability only; no Air role or native EW effect |
| Formation EW roles | E4-B local pass | `test_air_ew_formation.py`, cooperative environment | bounded self-protection permission; explicit communication inputs |
| Admission/terminal | queued | task cluster file | no promotion of Air capability or canonical modes |

## Scope

The ordered scope is passive ESM evidence, bounded jammer effects/resources,
temporal observation, cooperative command behavior, explicit action admission,
and named terminal acceptance. Real-platform EIRP/frequencies, emitter libraries,
antenna sidelobes, pulse processing, ghost tracks and calibrated J/S require
separate authored evidence and are not implied by this engineering model.

## Phase Plan

| Cluster | Goal | Entry | Exit | State |
| --- | --- | --- | --- | --- |
| E1 | RF/ESM contract and observation | merged jamming baseline | native negative cases, content validation, Python projection, state roundtrip | PR stack open |
| E2 | Jammer resources and effectiveness | E1 verified | bounded band/effect decision, cooldown/duty resource state and signed DRFM behavior with negative cases | PR #105 checks pass; review pending |
| E3 | EW temporal history | E1/E2 verified | opt-in history state, reset/replay, compatible policy extraction | local pass; PR #106 checks pass, review pending |
| E4-A | Shared command delivery | E3 verified | seeded delay/loss, TTL, receipts, node availability, Joint compatibility | local pass; PR #107 checks pass, review pending |
| E4-B | Cooperative Air EW | E4-A available | formation role orders, loss/expiry, reassignment and per-slot/resource isolation | local pass; PR pending |
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

### E2 jammer semantics

- A jammer with an explicit RF contract only affects a radar with a complete RF
  contract and positive band overlap. The overlap divided by jammer bandwidth
  scales the bounded burn-through proxy; disjoint bands have no effect. Legacy
  jammer definitions keep the existing bandwidth proxy.
- Jammer `rf_eirp_watts` remains an emission input for passive ESM. Jamming
  effectiveness continues to use the separate ERP-like `power_watts` input and
  its burn-through calibration; the two power quantities are not converted.
- `max_continuous_transmit_s` and `cooldown_s` are an optional paired budget.
  Omitted fields preserve unlimited legacy transmission; an exhausted burst
  stops and enters cooldown, and a manual stop also begins cooldown. Instrument
  state carries remaining burst time, remaining cooldown and snapshot time.
- Signed DRFM offsets alter the reported range of the same target only beyond
  burn-through and within the jammer beam. This does not create an independent
  ghost track.

### E3 temporal policy semantics

- `ew_state` remains opt-in. When it is enabled with `temporal_history_len > 1`,
  the environment adds `ew_state_history` and `temporal_valid_mask`; defaults
  and non-EW temporal observation keys remain unchanged.
- Reset pads are masked out of temporal attention. History belongs to each
  environment/formation slot and is cleared on reset; terminal observations keep
  the episode's final history before auto-reset starts a new one.
- The mask identifies real observation frames, not emitter presence, ESM
  confidence, or a valid RF detection. A reset's current frame remains valid
  even when EW fields contain their documented absent sentinels.
- `TemporalTransformerExtractor` encodes EW state per frame. The valid mask
  prevents padded frames from contributing as attention keys or receiving
  gradients. This demonstrates supported policy consumption, not training
  success or improved combat performance.

### E4-A shared delivery semantics

- `ScriptedCommandLink` carries opaque caller-owned immutable payloads over
  declared command edges. Defaults preserve lossless delayed delivery; optional
  loss is seeded, and expiry is measured from issue time with an exclusive end.
- Expiration wins at the exact delivery boundary. Unavailable sources/targets
  cancel their pending commands; restoration does not revive cancelled items.
  Air consumers remain responsible for clearing already accepted role leases.
- Receipts retain the latest 256 transport events; totals survive until reset.
  A delivery receipt does not mean that a domain model accepted the payload.
- The existing Joint graph adapter preserves command-edge authorization. Its
  durable inbox checks TTL again at the slower domain decision, so a previously
  delivered command can expire before consumption. This drop is a consumer
  filter, not a new transport receipt.

### E4-B formation role semantics

- `ew_formation_commanders` explicitly enables a same-team roster in the
  maintained cooperative environment with `air_ew_hybrid_v2`. Member names are
  scoped to each world; no role is implicitly assigned at reset.
- Only the first available declared commander can issue `emission_hold` or
  `self_protect` leases. Each order traverses the shared link and needs a positive
  finite TTL. A self-protection lease permits that aircraft's policy jammer
  request; it does not create requests or provide escort/support jamming.
- Expiry, declared member loss, or commander change removes accepted leases.
  Restoration requires a new order. Authority epochs reject delayed commands
  from an earlier command tenure; older delivery cannot overwrite a newer order.
- Filtering only covers action indices 14-15. Combat and local chaff/flare
  indices remain unchanged, and native systems retain resource/effect ownership.
  The default unconfigured path keeps its previous action behavior.
- Role receipts are bounded to 256 per world. Step info carries a per-member
  summary and the latest receipt at the action decision clock, not a new policy
  observation or a post-physics clock. Reset/auto-reset starts a fresh role/link
  lifecycle, while terminal info retains the old episode's receipt.
- Communication availability, delay and loss are explicit scripted-link inputs.
  This slice does not automatically map native DataLink/CommandLink status or
  infer aircraft destruction from hidden truth.

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

Local E2 mechanism validation, MSVC Release / Python 3.12:

- Rebuilt `ef_test`, `ef_py`, and `ef_runtime_host_candidate_test` from the
  E2 worktree after refreshing its configured build directory.
- Full `ef_test`: 257 cases, 155102 assertions passed.
- State-owner adapter suite: 16 cases, 489 assertions passed, including jammer
  budget reflection and post-EW instrument receipts.
- Eight focused Python modules passed 73 tests and 46 subtests, including EW
  suite schema, Air facade/observation, RL surface, bindings and replay.
- PR #103 and PR #105 checks are green. PR #104's fast, nightly, Windows and
  Linux checks pass; its CUDA job ended during toolchain installation after
  the job timeout. That required check remains unresolved and is not a source
  compile verdict. Reviews for PRs #103-#105 remain pending.

Local E3 temporal-policy validation, using the unchanged E2 native build:

- E3 temporal acceptance passed eight focused tests, including padding and
  gradient isolation, reset/terminal behavior, seeded replay, cooperative-slot
  isolation, configured PPO training, prediction, and checkpoint roundtrip.
- The broader temporal/EW compatibility selection passed 22 tests across the
  Air EW, temporal extractor and WorldBatch adapter suites.
- The maintained Air training-entry contract suite passed 21 tests and 42
  subtests. A strict load of an actual pre-E3 extractor state dict succeeded,
  and non-EW temporal forward outputs matched exactly in train and eval modes.
- `ruff check` and `git diff --check` passed for the E3 changes. Local execution
  used CPU Torch; CUDA device-bridge execution remains unverified locally.

Local E4-A delivery validation, using the unchanged E2 native build:

- Shared lifecycle, Joint coordination/consumer, native CommandLink QoS and
  tasking-contract architecture suites passed 87 tests. They cover delayed
  ordering, seeded loss/reset replay, expiry boundaries, unavailable-node
  cancellation, unrelated successor delivery, and TTL at domain consumption.
- No native source changed. This verifies shared transport and Joint regression;
  Air formation roles and native role/resource acceptance remain E4-B work.
- `ruff check` and `git diff --check` passed for the delivery changes.
- Document-link audit: 12 passed; the existing duplicate bilingual registry
  entry still fails (75 rows, 74 unique pair IDs), as recorded for E1.

Local E4-B formation validation, using the unchanged E2 native build:

- Final selection passed 109 tests across formation EW, cooperative EW demos,
  temporal state/policy, tasking architecture, WorldBatch adapter, shared/Joint
  command lifecycle and native CommandLink QoS.
- Tests observe delayed/lost/expired jammer permission in actual native state,
  commander loss and successor orders, member/world and chaff/flare isolation,
  exact seeded environment replay, reset, authority epochs, out-of-order
  rejection, and the default path's unchanged jammer requests.
- A broader run passed 95 tests and three subtests with three old cooperative
  failures. All three reproduced with the original E4-A environment source at
  `f931d84c1`: Python-only fire-authorization mutation, old warning step indices,
  and `int(None)` for an absent target. They are recorded residuals, not E4
  regressions or evidence of general cooperative suite closure.
- Native sources are unchanged. Lint and whitespace checks pass. The named
  terminal/capability verdict remains E6 work.

## Acceptance Gate

E1 can be mergeable only after RF sensitivity/band/legacy/malformed negatives,
confirmation/expiry/reset, same-source mount selection, state reflection, native
EW regressions and Python adapter/content tests pass on the published tree.
The first PR defines content/state/passive DTO contracts; the second activates
the sensing model, DTO projection and optional Python adapter.
Publication/checks/review remain distinct gates. E6, not E1, owns playability.

E2's local mechanism gate passes explicit RF overlap and off-band behavior,
budget stop/cooldown/recovery, instrument and state roundtrips, signed DRFM, and
the legacy jamming regressions. The PR stack still needs remote check closure and
review before merge.

## Residuals And Next Steps

- External/support-jammer composition is not implemented by this E2 slice and
  needs a separately scoped follow-up before that capability is claimed.
- Frequency overlap and burn-through remain engineering proxies, not calibrated
  J/S or platform performance. Independent DRFM ghost-track lifecycle remains
  out of scope.
- E3 is PR #106 based on PR #105; remote CI passes and review is pending.
- E3 keeps canonical action modes unchanged; model quality and learned-policy
  success still require their own evaluation evidence.
- E4-A adds shared opaque delivery with deterministic delay/loss, expiry,
  bounded receipts and node availability. Its Joint adapter regression passes;
  it does not assign Air EW roles or change native EW actions.
- E4-B locally verifies bounded role delivery, declared communication loss and
  reassignment, slot/resource isolation and replay. Native link-state mapping,
  aircraft-loss inference and external/support jamming remain separate work.
- The three reproduced old cooperative failures need a scoped follow-up before
  claiming that the full cooperative suite or broader C2 surface is closed.
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
