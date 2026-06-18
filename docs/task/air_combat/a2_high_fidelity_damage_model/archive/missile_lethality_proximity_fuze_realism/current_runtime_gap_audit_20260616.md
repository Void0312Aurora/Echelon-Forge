# Current Runtime Gap Audit

Status: `2026-06-16` PF-R2 pass / read-only audit for
[README.md](README.md).

Chinese companion: [current_runtime_gap_audit_20260616.zh.md](current_runtime_gap_audit_20260616.zh.md).

## Audit Boundary

This audit reads the current implementation and tests. It does not modify code,
tests, configs, training reward, or generated artifacts.

Primary implementation surface:

- `src/systems/combat/damage_system_common.h`

Primary tests observed:

- `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`
- `tests/runtime/air_combat/test_continuous_rod_surface.py`
- `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py`

## What The Current Runtime Already Does Well

| Runtime surface | Evidence | Why it is useful |
| --- | --- | --- |
| Fuze type routing | `damage_resolved_fuze_type` maps contact, radar/RF proximity, laser proximity, timed, and generic proximity. | Lets future contracts specialize evidence by sensor family. |
| Signature proxy | `damage_fuze_signature_evidence` records `target_rcs_aspect`, `target_projected_geometry`, or `generic_proximity`. | Gives an existing place to attach target-signature evidence. |
| Nearest approach event | `damage_record_nearest_approach_event` records local point, miss distance, closure, and aspect bucket. | Good diagnostic fact; should be retained. |
| Fuze evaluation event | `damage_record_fuze_evaluation_event` records armed/triggered/failure reason/delay/reliability/sample/trigger radius. | Good event boundary; can be expanded. |
| No-detonation no-load behavior | Existing tests assert no positive fragment/rod facts when fuze does not detonate. | Important invariant for any future surrogate. |
| Contact and timed fuze split | Existing tests distinguish proximity, contact, impact, and timed behavior. | Avoids collapsing all fuze types into a radius gate. |
| Warhead mechanism diagnostics | Continuous-rod tests check range, local aspect, orientation, and no-rod facts for non-rod cases. | Mechanism-specific downstream coverage already exists. |

## Core Proxy Gaps

| Gap | Current behavior | Why it is insufficient | Future surrogate direction |
| --- | --- | --- | --- |
| Closest point owns detonation geometry | `damage_effective_detonation_world_point` uses `proximity_min_local_*` for non-contact, non-timed proximity events when present. | Public fuze mechanisms make closest approach a diagnostic point, not necessarily the desired burst point. | Keep nearest approach as observation, but compute detonation point from sensor window, closing state, delay, and mechanism coverage. |
| Trigger radius is the primary gate | The runtime compares `detonation_metric_m` or `min_dist` against `trigger_radius_m` / `fuse_distance`. | Realistic proximity fuzing depends on target detection and lethal burst opportunity, not only center distance. | Add a sensor-opportunity gate with target surface/projection, sensor family, range window, crossing state, and terminal-track evidence. |
| Quality is mostly linear distance slack | `quality = 1 - distance / trigger_radius` for proximity cases. | This makes many cases differ weakly and can hide aspect/height/mechanism effects. | Replace or demote this to one input in a multi-factor opportunity score. |
| Probability floor is hard-coded | Proximity `base_hit = 0.35 + 0.65 * quality`. | This explains the observed near-miss floor and makes close detonations look artificially low or flat depending on quality/signature. | Move probability design into named detection/trigger/reliability stages; no unexplained floor. |
| Signature affects reliability, not detection state | Radar/laser signature scales effective reliability after range gate. | A real target-sensing surrogate should be able to fail detection before trigger, not only reduce final probability. | Emit `fuze_detection_event` or equivalent fields: detected, source, signature, threshold proxy, reason. |
| Terminal guidance support is binary and late | `proximity_fuze_has_terminal_guidance_support` can block after range-quality calculation. | Track validity should be visible as part of the sensor/target opportunity, not a hidden late veto. | Record terminal-track state before trigger, with reasoned no-detonation outcomes. |
| Delay is recorded but not used to choose an independent burst opportunity | Delay is applied after the trigger decision; proximity detonation point still tends to come from the nearest local point. | Public mechanisms describe delay as part of moving from first target detection to a more useful burst point. | For proximity fuzes, tie delay to a predicted detonation point along the missile trajectory or local sensor geometry. |
| Blast-fragmentation and continuous rod share the fuze gate | The fuze trigger path does not differ by warhead mechanism; mechanism differences mostly appear after detonation. | The useful burst interval depends on mechanism geometry. A continuous rod and a directional fragment band should not share the same opportunity test. | Add mechanism-specific coverage tests downstream of detection and before final detonation acceptance, or at least record coverage confidence. |
| Target center/hitbox distance can dominate target geometry | Proximity range is based on the runtime distance path; contact has surface evidence but proximity does not yet use the retained fine geometry by default. | A target-center distance can misread a large aircraft, especially near wings, nose, or high/low passes. | Use target surface/projection geometry as an opt-in input, with default-path acceptance separated. |

## Current Test Coverage To Preserve

| Test behavior | Keep | Extend |
| --- | --- | --- |
| Radar proximity delay records fuze and effects events | yes | Add detection/trigger sub-reasons and detonation-point source. |
| Reliability failure records no-detonation and no positive loads | yes | Split detection failure from trigger/reliability failure. |
| Contact fuze does not trigger from near-miss radius | yes | Ensure proximity-specific surface logic does not break contact semantics. |
| Timed fuze detonates independent of proximity gate | yes | Keep timed path outside sensor window logic. |
| Continuous rod margin changes with range/aspect/orientation | yes | Add fuze opportunity checks that respect rod cutting band. |
| Non-rod and no-detonation cases carry zero rod facts | yes | Keep no-load invariant after new fuze failure modes. |

## Audit Conclusion

The current runtime has a good explainability backbone, but the triggering logic
is still a nearest-distance proxy. The next design should not discard the event
chain. It should insert an explicit sensor-opportunity / detection / trigger /
burst-timing layer between nearest approach and effects.

PF-R2 is complete as a read-only gap audit. Implementation remains held.
