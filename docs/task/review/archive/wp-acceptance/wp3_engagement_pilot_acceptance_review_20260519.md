# WP3 Engagement Pilot — Acceptance Review

Status: `2026-05-19` acceptance review completed.
Scope: WP3 engagement pilot implementation — contracts, adapters, facade export, Python bindings, tests, smoke promotion.

Related documents:

- [WP3 task family](../../task/simulation_architecture/engagement_pilot_wp3_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [WP1 pipeline inventory](../../task/simulation_architecture/pipeline_inventory_wp1_20260519.md)
- [WP2 contract freeze](../../task/simulation_architecture/contract_freeze_wp2_20260519.md)

## 1. Review Scope

- `src/runtime/contracts/engagement_contracts.h` — 7 stable DTOs (TrackPacket, LaunchRequest, LaunchEvent, MunitionLifecyclePacket, EffectsEvent, DamageReport, DiagnosticsTrace)
- `src/core/engine/weapon_launch_adapter.h` — header-only conversion seam (7 snapshot types, 7 inline converters)
- `src/runtime/facade/runtime_facade.h` / `.cpp` / `types.h` — EngagementBatchRequest, EngagementEventPacket, export_engagement_event_packet()
- `src/interfaces/python/bindings_runtime.cpp` — nanobind exposure of all 7 DTOs + EngagementEventPacket + RecentEngagementEvents
- `tests/runtime/engagement/` — 25 tests across 8 files covering contracts, air/naval adapters, lifecycle, effects, damage, diagnostics, live capture, facade export
- `tests/runtime/facade/test_runtime_facade.py` — 10 tests including engagement packet shell and export validation
- `tests/architecture/` — 15 layering and target readiness tests
- `tests/smoke/ci_smoke_suite.json` — smoke promotion of engagement test directory

## 2. Test Execution Evidence

```
tests/runtime/engagement/                    25 passed in 0.27s
tests/runtime/facade/test_runtime_facade.py   10 passed in 0.30s
tests/architecture/                           15 passed in 0.15s
────────────────────────────────────────────────────────
Total                                         50 passed, 0 failed
```

All tests run locally without RL training dependencies. No imports of `torch`, `gym`, `gymnasium`, or any RL-specific module.

## 3. Acceptance Gates

### Gate 1 — Shared LaunchEvent shape across platform families

**PASS.** Air pylon launch (F-16 hardpoint via `fire_missile()`) and naval mount/VLS launch (DDG Mk45 gun via `fire_naval_weapon()` and DDG VLS SAM via `fire_missile()`) both map to the identical `LaunchRequest` / `LaunchEvent` pair.

Evidence:
- [test_air_launch_adapter.py](../../../tests/runtime/engagement/test_air_launch_adapter.py) — `station_id="air:pylon"`, `requested_munition_family="missile"`
- [test_naval_launch_adapter.py](../../../tests/runtime/engagement/test_naval_launch_adapter.py) — `mount_id="mk45_gun"` and `mount_id="forward_vls_sam"`
- Both use `ef_py.LaunchRequest` and `ef_py.LaunchEvent` — no type fork

### Gate 2 — Explicit acceptance/rejection reasons

**PASS.** `LaunchEvent.accepted` is an explicit bool. `LaunchEvent.rejection_reason` carries the reason string (`"no_active_track"` for rejected, `""` for accepted). No implicit boolean return value survives as the maintained contract path.

Evidence:
- [test_air_launch_adapter.py:213](../../../tests/runtime/engagement/test_air_launch_adapter.py#L213): rejected launch asserts `rejection_reason == "no_active_track"`
- [test_naval_launch_adapter.py:325-326](../../../tests/runtime/engagement/test_naval_launch_adapter.py#L325-L326): VLS without track asserts `rejection_reason == "no_active_track"`

### Gate 3 — Ammo, cooldown, launcher, munition, and ancestry in event fields

**PASS.** `LaunchEvent` carries `ammo_delta`, `cooldown_delta_s`, `selected_launcher`, `selected_munition`, `spawned_munition` (EngagementEntityRef), and `has_spawned_munition`. `MunitionLifecyclePacket` back-links to `launch_event_id`.

Evidence:
- [test_naval_launch_adapter.py:225-226](../../../tests/runtime/engagement/test_naval_launch_adapter.py#L225-L226): `ammo_delta == -1`, `cooldown_delta_s == 3.5`
- [test_air_launch_adapter.py:180-182](../../../tests/runtime/engagement/test_air_launch_adapter.py#L180-L182): `ammo_delta == -1`, `cooldown_delta_s == 0.75`

### Gate 4 — Munition lifecycle export does not expose full ECS internals

**PASS.** `MunitionLifecyclePacket` exports 17 normalized semantic fields (`seeker_mode`, `guidance_cadence_s`, `track_memory_state`, `fuel_remaining_fraction`, `burnout`, `max_flight_time_s`, `fuze_state`, etc.). The ~75-field `Missile` ECS component is not leaked.

Evidence:
- [test_munition_damage_adapter.py:84-118](../../../tests/runtime/engagement/test_munition_damage_adapter.py#L84-L118): field selection and normalization from `debug_get_missile_runtime_state()` raw dict into `MunitionLifecyclePacket`

### Gate 5 — Damage visibility uses DamageReport

**PASS.** `DamageReport` carries `hp_delta`, `system_health_delta`, `platform_damage_state_delta`, `mission_kill`, `mobility_kill`, `sensor_kill`, `survivability_kill`, `loss_state_from`, `loss_state_to`, `destroyed`. No reliance on raw debug health reads as the public contract.

Evidence:
- [test_munition_damage_adapter.py:209-226](../../../tests/runtime/engagement/test_munition_damage_adapter.py#L209-L226): DamageReport construction from health/damage state with semantic kill state mapping
- [test_live_engagement_event_capture.py:163-188](../../../tests/runtime/engagement/test_live_engagement_event_capture.py#L163-L188): `debug_apply_proximity_hit` produces EffectsEvent + DamageReport pair, `hp_delta < 0.0`, linked by `source_event_id`

### Gate 6 — DiagnosticsTrace chain linkage

**PASS.** `DiagnosticsTrace` struct contains `trace_id`, `parent_trace_id`, `chain_id`, `track_id`, `launch_request_id`, `launch_event_id`, `munition` (EngagementEntityRef), `effects_event_id`, `damage_report_id`, `observation_packet_version`. All 7 link fields are verified end-to-end.

Evidence:
- [test_diagnostics_trace_contract.py:133-151](../../../tests/runtime/engagement/test_diagnostics_trace_contract.py#L133-L151): verifies every link field matches the corresponding packet ID in a single chain

### Gate 7 — Explicit facade and Python access

**PASS.** `RuntimeFacade::export_engagement_event_packet()` is the facade-level API. `RuntimeFacade::runtime()` escape hatch is documented as "Compatibility escape hatch for diagnostics and legacy adapters only." Python bindings expose all 7 DTOs + `EngagementEventPacket` + `RecentEngagementEvents` via `ef_py`. Architecture tests enforce facade layering compliance.

Evidence:
- `src/runtime/facade/runtime_facade.h:33-36`: explicit escape-hatch documentation
- [test_runtime_facade_layering.py](../../../tests/architecture/runtime_facade): 9 layering tests pass — escape hatch stays in adapter, VecEnv does not cache raw handles, leader runtime does not reach raw world handles, contract headers do not include engine headers
- [test_facade_engagement_export.py:173-236](../../../tests/runtime/engagement/test_facade_engagement_export.py#L173-L236): multi-world export retags `spawned_munition.world_index` and `diagnostics_trace.munition.world_index` for `world_index=1`
- `RecentEngagementEvents` only carries `launch_events`, `effects_events`, `damage_reports`, and `diagnostics_traces`, so there is no `launch_requests` or `munition_lifecycle_packets` retagging path in the recent-event buffer.

### Gate 8 — Local validation without RL dependencies

**PASS.** All 50 tests complete in under 0.7 seconds. No RL imports. `ci_smoke_suite.json` includes `tests/runtime/engagement` as a directory path.

Evidence:
- `tests/smoke/ci_smoke_suite.json:7`: `"tests/runtime/engagement"` entry
- Test suite output confirms zero RL imports

## 4. Branch Deliverable Confirmation

| Branch | Artifact | Status |
|--------|----------|--------|
| WP3-A | `engagement_contracts.h` — 7 DTOs, no `core/` or `engine/` includes | Verified: 4 contract shape tests pass |
| WP3-B | `EngagementBatchRequest`, `EngagementEventPacket`, `export_engagement_event_packet()` | Verified: 2 facade export tests pass, include flags honored |
| WP3-C | Python bindings for all 7 DTOs + `RecentEngagementEvents` | Verified: all tests construct and read DTO fields via `ef_py` |
| WP3-D | Air pylon launch → `LaunchRequest`/`LaunchEvent` | Verified: 2 air adapter tests (accepted + rejected) |
| WP3-E | Naval gun/VLS launch → same `LaunchEvent` shape | Verified: 3 naval adapter tests (gun accepted + VLS accepted + VLS rejected) |
| WP3-F | Munition lifecycle and effects/damage adapters | Verified: 2 tests (lifecycle normalization + synthetic effects/damage) |
| WP3-G | Diagnostics trace full-chain linkage | Verified: 1 test verifies 7 link fields |
| WP3-H | Smoke suite promotion | Verified: `ci_smoke_suite.json` includes `tests/runtime/engagement` |
| WP3-I | Integration and docs | Verified: 50 tests green, no shared-file conflicts |

## 5. Outside WP3 Acceptance (Documented Follow-up)

Per [WP3 task document Section 9](../../task/simulation_architecture/engagement_pilot_wp3_20260519.md#L236-L242):

1. **Real missile terminal effects/damage capture.** Current coverage: legacy launch, naval direct-fire, debug proximity-hit paths. Terminal effects from the maintained guidance and effects systems are deferred to WP4/WP5.
2. **Recent-event storage strategy.** Currently a bounded compatibility buffer (`kMaxRecentEngagementEvents = 64`). Decision on migrating to a formal event queue owner is deferred to WP4/WP5.

## 6. Architecture Alignment Assessment

The implementation respects the architecture design rules documented in the baseline:

- **Law #3** (components are data contracts): `engagement_contracts.h` is pure DTO, no per-tick behavior.
- **Law #7** (facade does not copy every kernel method): `export_engagement_event_packet()` is a use-case API, not a 1:1 kernel method mirror.
- **Law #8** (interfaces and Python adapters translate formats): `weapon_launch_adapter.h` is a header-only conversion seam, no simulation semantics.
- **Law #10** (domain extensions declare pipeline participation): `LaunchRequest` and `LaunchEvent` cover `P7 FireControlLaunch`, `MunitionLifecyclePacket` covers `P8 MunitionLifecycle`, `EffectsEvent` and `DamageReport` cover `P9 EffectsDamage`, `DiagnosticsTrace` covers `P10 ObservationExport`.

The current gap between the architecture's temporal DAG target and the linear `ecs.progress()` execution is acknowledged in the architecture document itself (Law #11) and tracked under WP4/WP5 — it is not a WP3 scope issue.

## 7. Conclusion

WP3 meets all 8 acceptance gates and is accepted. The cross-domain engagement lifecycle — air pylon launch and naval mount/VLS launch — shares one typed contract vocabulary without an "air weapon" or "naval weapon" private runtime path. The contract layer has zero dependency on `core/engine/*`. Facade access is explicit and the escape hatch is documented. Diagnostics can explain the full chain from track to observation. Local validation runs without RL dependencies. WP4/WP5 items remain outside WP3 acceptance.
