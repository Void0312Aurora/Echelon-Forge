# A2 MLF-2 Dispatch Queue

Status: `2026-06-09` archived dispatch queue; `MLF-2B`, `MLF-2C`, `MLF-2D`, `MLF-2E`, `MLF-2F`, and `MLF-2G` are accepted. No packet is currently running.

Chinese main text: [missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.zh.md)

Parent task clusters: [missile_lethality_geometry_fuze_task_clusters_20260609.md](missile_lethality_geometry_fuze_task_clusters_20260609.md)

## Boundary

This queue is only for MLF-2 approach geometry and fuze evaluation. Dispatches must not create a new conversation thread and must not enter fragmentation, continuous rod, structural breakup, debris/wreck, Pk, or AIM-120C/MQ-9 case calibration.

## Dispatched Packets

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-2B-X1` | `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only inspection; no runtime/test/probe edits in this packet | Find the shortest controlled geometry path and state whether existing fixtures can be reused; this packet is read-only and must not write fuze physics. | accepted |
| `MLF-2B-W1` | `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`; `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` | Implement the smallest live missile controlled-geometry test fixture, varying at least two of range/aspect/closure/altitude offset and validating geometry observations only. | accepted |
| `MLF-2C-X1` | `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only writer-path audit; no runtime/contract/test edits | Find the minimum producer path for writing `NearestApproachEvent` in the live missile lifecycle. | accepted |
| `MLF-2C-W1` | `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `src/components/combat/weapon.h`; `src/core/interfaces/engagement_event_recorder.h`; `src/core/engine/simulation_kernel_engagement_event_store.h`; `src/core/engine/simulation_kernel_engagement_event_store.cpp`; `src/core/engine/simulation_kernel_weapon_release_service.cpp`; `src/interfaces/python/bindings_core.cpp`; `src/systems/combat/damage_system.h`; related geometry/fuze tests | Write nearest-approach events so no-detonation cases still record nearest point and reason; nearest-point time comes from the point update moment. | accepted |
| `MLF-2D-X1` | `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only writer-path audit; no runtime/contract/test edits | Find the minimum producer path for writing `FuzeEvaluationEvent` in the live missile lifecycle. | accepted |
| `MLF-2D-W1` | `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | `src/core/interfaces/engagement_event_recorder.h`; `src/core/engine/simulation_kernel_engagement_event_store.h`; `src/core/engine/simulation_kernel_engagement_event_store.cpp`; `src/systems/combat/damage_system.h`; related geometry/fuze tests | Write armed, trigger, no-trigger, delay, and failure reasons. | accepted |
| `MLF-2E-X1` | `MLF-2E Diagnostics Projection` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only diagnostics/probe path audit; no runtime edits | Find the minimum path for process probe / diagnostic export consumption of nearest-approach and fuze-evaluation events. | accepted |
| `MLF-2E-W1` | `MLF-2E Diagnostics Projection` | main thread | `tools/diagnostics/air_combat_stage0_process_probe.py`; `tests/runtime/air_combat/test_diagnostics_probe_contracts.py` | Export geometry/fuze stage rows per munition without relying on old `last_effect_*`. | accepted |
| `MLF-2F-I1` | `MLF-2F Runtime Handoff Gate` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | read-only weapon lifecycle/effects invocation audit; no runtime edits | Audit the minimum gate where only detonation enters the effects model and no-trigger paths have event, reason, and no effects. | accepted |
| `MLF-2F-W1` | `MLF-2F Runtime Handoff Gate` | main thread | `tests/runtime/air_combat/weapon_guidance_realism/fuze.py` | Pin runtime handoff gate behavior: triggered path has one effects/damage record, contact near-miss has no effects/damage record, reliability failure remains a zero-damage transitional record. | accepted |
| `MLF-2G-C1` | `MLF-2G Acceptance And Archive Prep` | main thread | this subproject README/status/task cluster/dispatch queue/archive index; A2 README | Summarize evidence and update accepted/held state plus residual map. | accepted |

## Current Dispatch Recommendation

No packet is currently running. `MLF-2G-C1` is accepted; this queue is closed with the MLF-2 archive.

Follow-on work must not add runtime features, enter warhead effects, or expand MLF-2 into kill, breakup, or Pk conclusions in this queue.

## Returned Dispatch Records

### MLF-2B-X1

Worker returned `pass` and touched no files.

- Usable shortest path: live `sim.fire_missile`, `_spawn_geometry_pair`, truth-track drive, and existing `EffectsEvent` geometry fields.
- Controllable inputs: initial range, aspect/lateral placement, closure, and altitude offset; target pitch/roll remain limited in the live helper.
- Standard `NearestApproachEvent` / `FuzeEvaluationEvent` vectors are declared and bound, but current search found no live writer.
- Conclusion: proceed to `MLF-2B-W1` smallest test fixture; `MLF-2C` still waits for W1 geometry fixture acceptance.

### MLF-2B-W1

Worker returned `pass`; main thread revalidation passed.

- Touched files: `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`, `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`.
- Controlled inputs: range, closure, aspect/lateral placement, and altitude offset.
- Observed fields: initial truth detection range/closing_speed/bearing/elevation, missile runtime `proximity_min_dist_m`, and `EffectsEvent.nearest_approach_time_s`, `closure_mps`, `detonation_local_up_m`, `miss_distance_m`.
- Main-thread revalidation: `py_compile` passed; 2 focused pytest tests passed; relevant diff check passed.
- Limitation: target pitch/roll is not yet in live `_spawn_geometry_pair`; standard `NearestApproachEvent` / `FuzeEvaluationEvent` writers are still not live.

### MLF-2C-X1

Worker returned `pass` and touched no files.

- Standard `NearestApproachEvent` / `FuzeEvaluationEvent` structs, containers, and Python bindings already exist.
- No live `nearest_approach_events.push` / writer path exists yet; the event store currently writes only launch, effects, and damage.
- Recommended implementation: add a nearest-approach record interface to `engagement_event_recorder`, let the event store assign event id, resolve launch/chain/parent, then push/cap/sort `nearest_approach_events`.
- Recommended call site: `damage_system.h` `ProximityFuze` pass-by / fuze decision point, where nearest local point, miss distance, closure, and target information are available.
- Limitation: guidance max-flight-time expiry currently lacks recorder access and is not covered by W1.

### MLF-2C-W1

Worker returned `pass`; main thread revalidation passed, and main thread added nearest-point time bookkeeping before revalidating again.

- Touched files: `src/components/combat/weapon.h`, `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.h`, `src/core/engine/simulation_kernel_engagement_event_store.cpp`, `src/core/engine/simulation_kernel_weapon_release_service.cpp`, `src/interfaces/python/bindings_core.cpp`, `src/systems/combat/damage_system.h`, `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`, `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`, `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`.
- Implementation: added nearest-approach recorder interface and event-store writer; export sorting includes `nearest_approach_events`; `damage_system.h` writes nearest-approach events for missed trigger radius, no terminal track, no detonation, and fuze armed paths.
- Main-thread addition: `Missile` now records `proximity_min_time_s` when the nearest point is updated; nearest-approach events and transitional effects fields use that time instead of always using the terminal decision frame.
- Main-thread revalidation: `py_compile` passed; `cmake --build build-workshop --target ef_py -j2` passed; 3 missile geometry/fuze focused pytest cases passed; `tests/runtime/engagement/test_live_engagement_event_capture.py -q` passed with 7 tests; relevant diff check passed.
- Limits: no `FuzeEvaluationEvent` writer yet; max-flight-time expiry still lacks recorder access; legacy `EffectsEvent` fields remain transitional observation fields.

### MLF-2D-X1

Worker returned `pass` and touched no files; main thread verified that event structures and bindings exist.

- Existing surface: `FuzeEvaluationEvent` in `src/runtime/contracts/engagement_contracts.h`; `fuze_evaluation_events` containers in `engagement_event_types.h` and `runtime_facade_types.h`; Python bindings in `bindings_runtime.cpp` and `bindings_core.cpp`.
- Gap: no `record_fuze_evaluation_event(...)` recorder interface; no event-store writer/push/cap; `export_recent_events_sorted()` does not sort `fuze_evaluation_events`.
- Recommended implementation: add `EngagementFuzeEvaluationEventRecord`; let the event store assign ids, resolve launch chain, and prefer the same-munition latest `NearestApproachEvent` as parent.
- Recommended call sites: `damage_system.h` branches for `miss_outside_trigger_radius`, `fuze_no_terminal_track`, `fuze_no_detonation`, and `fuze_armed`.
- Limits: max-flight-time expiry still lacks recorder access; timed fuze should be optional/held in W1 and must not be conflated with nearest-approach semantics.

### MLF-2D-W1

Worker returned `pass`; main thread revalidation passed.

- Touched files: `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.h`, `src/core/engine/simulation_kernel_engagement_event_store.cpp`, `src/systems/combat/damage_system.h`, `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`, `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`, `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py`.
- Implementation: added `EngagementFuzeEvaluationEventRecord` and `record_fuze_evaluation_event(...)`; event store writes/caps/sorts `fuze_evaluation_events`; parent event prefers the same-munition latest `NearestApproachEvent`.
- Branch coverage: `miss_outside_trigger_radius`, `fuze_no_terminal_track`, `fuze_no_detonation`, and `fuze_armed` each emit one fuze-evaluation event; delayed damage application does not emit a duplicate event.
- Main-thread revalidation: `py_compile` passed; `cmake --build build-workshop --target ef_py -j2` passed; 4 missile geometry/fuze focused pytest cases passed; `tests/runtime/engagement/test_live_engagement_event_capture.py -q` passed with 7 tests; relevant diff check passed.
- Limits: timed fuze evaluation remains held; max-flight-time expiry still lacks recorder access; diagnostics probe does not yet consume `FuzeEvaluationEvent`.

### MLF-2E-X1

Worker returned `pass` and touched no files.

- Current state: `tools/diagnostics/air_combat_stage0_process_probe.py` already has `nearest_approach` and `fuze` diagnostic rows, but they were primarily projected from `EffectsEvent`; no-effect no-trigger / near-miss paths could not be read completely.
- Gap: the probe did not consume `nearest_approach_events` or `fuze_evaluation_events`.
- Recommended implementation: standard events first; old `EffectsEvent` projection only as fallback when the same chain/munition lacks standard nearest/fuze rows.
- Limits: do not change runtime physics, effects model, reward, or infer kill/crash/Pk.

### MLF-2E-W1

Main thread implemented and accepted.

- Touched files: `tools/diagnostics/air_combat_stage0_process_probe.py`, `tests/runtime/air_combat/test_diagnostics_probe_contracts.py`.
- Implementation: `_lethality_chain_rows()` now prioritizes `NearestApproachEvent` / `FuzeEvaluationEvent`; old `EffectsEvent` nearest/fuze projection is fallback only for the same chain/munition; new diagnostic fields include `closure_mps`, `aspect_bucket`, `fuze_armed`, `fuze_triggered`, `fuze_failure_reason`, `fuze_reliability`, `fuze_sample`, and contact evidence.
- Test coverage: standard-event-only no-detonation path; standard events suppress duplicate effects fallback rows; existing fallback and CSV output remain.
- Main-thread revalidation: `py_compile` passed; `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q` passed with 17 tests.
- Limits: platform/lifecycle remains projected from `DamageReport`; runtime handoff gate is not implemented; reward and effects model are unchanged.

### MLF-2F-I1

Worker returned `pass` and touched no files.

- Effects-model call point: `damage_system.h` calls `effects_ref->model->on_proximity_hit(...)` only in the `fuze_delay_armed` block after `fuze_detonation_time_s` is reached.
- Triggered path: `fuze_armed` writes nearest-approach and fuze-evaluation events, then later enters the existing effects model once and records one `EffectsEvent` / `DamageReport`.
- No-trigger paths: `miss_outside_trigger_radius` records events and destroys the missile without effects-model call or effects/damage records; `fuze_no_terminal_track` and `fuze_no_detonation` do not call the effects model, but still keep zero-damage transitional `EffectsEvent` / `DamageReport`.
- Limits: timed fuze standard event coverage remains held; max-flight-time / guidance expiry still lacks recorder access.

### MLF-2F-W1

Main thread hardened tests and accepted the slice.

- Touched file: `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`.
- Implementation: tightened existing fuze tests so delayed triggered path has exactly one nearest-approach event, one fuze-evaluation event, one effects event, and one damage report; reliability failure is one zero-damage transitional record; contact near-miss has no effects event and no damage report.
- Main-thread revalidation: `py_compile` passed; 3 focused fuze gate pytest cases passed.
- Limits: runtime physics, effects model, and reward were not changed; zero-damage transitional records remain until downstream consumers fully migrate.

### MLF-2G-C1

Main thread executed and accepted this packet.

- Touched files: this subproject README, current status, task clusters, dispatch queue, archive index, and A2/MLF-1 navigation READMEs.
- Implementation: moved the complete MLF-2 evidence package under `archive/mlf_2_geometry_fuze_accepted_20260609/`; converted the current MLF-2 directory to a lightweight pointer; synchronized accepted/held status and the MLF-3+ residual map.
- Acceptance conclusion: MLF-2 can explain missile nearest point, fuze arming/trigger/failure reason, and detonation handoff; it still does not implement warhead effects, fragmentation, debris/wreck, Pk, or weapon-specific lethality.
- Limits: timed fuze, guidance-expiry recorder access, zero-damage transitional record removal, and finer target attitude remain future-phase work.

## Worker Packet Contract

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Integration Notes

- The main thread owns returned-packet acceptance and queue updates.
- Status lines, task-cluster status, and parent README updates must be serial after acceptance.
- No worker packet is currently running, and the queue is closed with the MLF-2 archive.
- If a worker finds that current runtime cannot reproduce controlled geometry input, it should return blocked/partial with the gap instead of routing around it through a direct-kill rule.
