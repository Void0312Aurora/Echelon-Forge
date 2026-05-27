# A2 High-Fidelity Air-Combat Damage Model

Status: Phase 0 accepted on `2026-05-26`; the Phase 1 minimal patch is in progress with focused tests passing; Phase 2 has moved from generated fallback into the first authored aircraft-hitbox coverage plus an aircraft-specific `AircraftDamageState` overlay, overlay-driven flight/propulsion/sensor derivation, a minimal high-energy envelope loop for damaged-structure degradation, a minimal fire/fuel-leak/hydraulic cascade timeline, and a minimal named-control-component axis/asymmetry overlay for aileron/elevon/rudder/flap/thrust-vector/cyclic/collective damage; Phase 3 has moved from minimal `WarheadProfile` plumbing into the first warhead-family effects-distribution patch, a warhead-family spatial-footprint projection loop, minimal relative-velocity-axis coupling, explicit `EffectsEvent` geometry evidence, parameterized fragment/continuous-rod spatial-sampling evidence, parameterized detonation-attitude orientation-pattern evidence, an auditable hitbox-armor / projected-exposure / warhead-mechanism sampling scaffold, the first mechanism-specific component-threshold scaffold, a synthetic component-failure probability sampling scaffold, explicit `FuzeProfile` evidence, minimal proximity-fuze delayed-detonation scheduling, the first fuze-type trigger-semantics branch, component-level geometry entries for representative F-16/Su-35S/MQ-9/MH-60R/E-3 components, primary-component evidence and candidate component mechanism-load rows on `EffectsEvent`, minimal critical/redundancy semantics for component-failure probability, a first `ComponentDamageState` memory surface for named redundancy-group availability, and a minimal component `dependencies` propagation scaffold into related systems and aircraft overlays; Phase 5 has started a synthetic vulnerability-evidence scaffold plus a calibrated-evidence gate, and vulnerability profile/evidence/authority/scale fields now reach `EffectsEvent`; structured-air physical effects now have behavior/static guards proving they do not directly write RL `Score`, and the 1v1 consumer now reads `DamageReport` for terminal/objective semantics plus minimal nonterminal damage shaping. The current loop covers PN miss-distance baselines, HP-first bypass reversal for structured aircraft, live-missile `EffectsEvent`/`DamageReport` recording, structured-air score-authority guards, aircraft damage-state synchronization, nose/fuselage/wing subsystem effect differentiation, F-16/Su-35/MQ-9/MH-60R/E-3 migration onto authored structured hitboxes, all current aircraft unit JSONs carrying 20+ representative components with full mechanism thresholds and component centers inside their parent hitboxes, broad blast/fragmentation near-miss projection that preserves regional hitbox coverage instead of being narrowed by component candidates, air-specific structure/flight-control/hydraulic/roll-pitch-yaw-control/asymmetry/propulsion/fuel/avionics/crew overlay evidence, overlay-derived FlightModel/Propulsion/fuel-leak and sensor range/Pd/noise/track-memory constraints, damaged-airframe high dynamic pressure/Mach exposure, real `FuelSystem` / `Mass` fuel depletion from fuel leaks, time-cascade fire/hydraulic/fuel propagation into structure/avionics/crew/flight-control/platform capability, auditable warhead family/mass/lethal-radius/synthetic provenance and fuze type/radius/delay/reliability/synthetic provenance in missile runtime, effects events, diagnostics-only local-hit effects tests, distance-attenuated near-miss projection tests, warhead-family footprint tests, continuous-rod velocity-axis and detonation-attitude-axis near-miss direction tests, parameterized fragment/rod spatial-sampling tests, armor/exposure mechanism sampling tests, component-threshold mechanism-sensitivity tests, component-failure probability sampling tests, database F-16/Su-35S and representative UAV/helicopter/C2 primary-component evidence tests, named control-component roll/pitch/yaw authority tests, component critical/redundancy probability modulation tests, cumulative component-integrity and named redundancy-group availability tests, component-dependency propagation tests into hydraulic/flight-control/avionics overlays, fuze runtime/event tests, fuze delay scheduling tests, contact-fuze near-miss non-trigger tests, timed-fuze independent-delay detonation tests, `EffectsEvent` miss distance/local detonation point/detonation attitude/closure/velocity-axis/orientation-axis/direct-or-projected hit/fuze/spatial-effect/armor-coupling/exposure/mechanism-effect/warhead-spatial-sampling/component-threshold/component-identity/component-mechanism-load-rows/component-failure/component-integrity/redundancy-group/vulnerability evidence, an F-16 synthetic vulnerability profile that modulates structured damage by warhead/aspect/closure/near-miss evidence, a guard proving synthetic vulnerability is not Pk or deterministic-fuze authority, and a one-shot consumer guard for nonterminal `DamageReport` shaping.

Inputs:

- [Air-combat damage model evaluation](../../../forward/air_combat_damage_model_evaluation_20260522.md)
- [Codebase cross-evaluation](../../../forward/air_combat_damage_model_cross_eval_20260522.md)

This subproject supports the staged `1v1` realism curriculum, but it is not an RL-convenience track. Weapon events must first produce physically interpretable local structure and subsystem damage. Platform-level kill state is then derived from that state. RL rewards, curricula, and legacy `health` readouts consume these results; they do not define the physical damage authority.

## Design Stance

- `Health.current_hp` may remain as a compatibility readout, but it is not the air-combat kill authority.
- Authoritative effects originate from weapon events: impact/proximity detonation, fuze state, miss distance, relative geometry, warhead family, and target vulnerability.
- Damage first mutates structure, propulsion, fuel, sensors, flight controls, cockpit/pilot state, and related subsystems.
- Kill state is derived from subsystem and structure state, not from direct scalar `damage` subtraction.
- Randomness is allowed only for explicitly modeled uncertainty or physical sampling.
- RL shaping belongs in consuming layers, not in the physical effects model.

## Phase 0 Gates

Phase 1 code must not begin until these audits are closed and recorded. `A2-P0.1` through `A2-P0.6` are now closed in the Phase 0 audit:

- `PlatformLossState` enum audit, especially raw integer comparisons and append-only or overlay semantics for `ForcedLanding`;
- Python health observer audit for `health > 0`, `get_unit_health`, and `is_unit_active` callers;
- `ShipPlatform` filter audit for `NavalDamageStateUpdate` and adjacent ship-only systems;
- aircraft JSON inventory and authored-hitbox versus generated-fallback decision;
- `Score` write-point audit and event-driven scoring consumer plan;
- PN miss-distance benchmark matrix before deterministic fuze work.

Current Phase 0 evidence:

- [Phase 0 preflight audit - 2026-05-26](phase0_preflight_20260526.zh.md)

## Implementation Phases

| Phase | Status | Goal | Primary Risk |
|---|---|---|---|
| `Phase 0 Preflight` | accepted | Close audits and guidance baselines. | Missing evidence leads to unsafe behavior changes. |
| `Phase 1 Aircraft Structured Damage` | minimal patch in progress | Reverse HP-first bypass, spawn aircraft damage state, derive kill state from damage state. | Medium-high behavior change. |
| `Phase 2 Aircraft Subsystem Effects` | overlay dynamic coupling started | Add propulsion, flight-control, structure, fuel, sensor, avionics, and cockpit effects. | Flight dynamics and sensor consumers. |
| `Phase 3 Warhead Profiles` | profile fuze trigger semantics started | Replace scalar `damage` with blast/fragment/rod/HTK profiles, explicit fuze profiles, delayed detonation scheduling, fuze-type trigger semantics, and family/velocity-axis/armor/exposure/component-specific mechanism-threshold/component-failure evidence. | Content and geometry calibration. |
| `Phase 4 Deterministic Fuze` | held/deferred | Replace RNG hit probability with geometry-first fuze/effects. | PN baselines are closed; still needs warhead/fuze/vulnerability calibration. |
| `Phase 5 Vulnerability Evidence` | synthetic evidence scaffold started | Add target/weapon/aspect/closure evidence and Pk calibration. | Data provenance. |

## Non-Goals

- Do not simplify damage physics for short training convenience.
- Do not treat a scalar `damage` value as a high-fidelity warhead model.
- Do not keep `health <= 0` as authoritative for structured aircraft damage.
- Do not remove RNG fuze before PN miss-distance evidence exists.
- Do not renumber shared loss-state enum values during Phase 0.

## Acceptance Signals

- A structured aircraft target cannot be killed through the HP-first bypass.
- Missile events produce inspectable `EffectsEvent`, `DamageReport`, and subsystem mutation.
- `EffectsEvent` exposes miss distance, target-body detonation point, detonation attitude, closure speed, and missile velocity-axis evidence for later fuze/Pk calibration.
- `EffectsEvent` exposes direct/projection hit form, spatial effect scale, armor-coupling scale, projected-exposure scale, mechanism-effect scale, and uncalibrated mechanism-load evidence such as fragment energy, penetration margin, blast overpressure/impulse, and continuous-rod cut margin.
- `EffectsEvent` exposes warhead spatial sample count, estimated fragment/rod hits, hit fraction, energy scale, pattern scale, detonation orientation axis, and orientation pattern scale as parameterized evidence; these fields are not calibrated fragment-cloud, blast, or continuous-rod authority.
- `EffectsEvent` exposes component-threshold scale, proving the event did not treat every protected system as the same generic scalar.
- `EffectsEvent` exposes component-failure probability/source/calibrated/dataset/sample/count as component-level probability evidence; the synthetic sigmoid path consumes uncalibrated mechanism-load evidence, authorized descriptor rows can still override the probability and are auditable as `vulnerability_evidence_row`, but test fixtures are not calibrated Pk authority.
- `EffectsEvent` exposes component hit count, candidate component mechanism-load rows, and primary component identity so component geometry and row-level load selection are auditable outside logs.
- `EffectsEvent` exposes primary component integrity, primary component mechanism-load fields, and named redundancy-group availability/member/failure counts, so repeated component damage has runtime memory instead of being only a one-shot probability discount.
- `EffectsEvent` exposes vulnerability profile/evidence/authority/provenance/aspect/closure/scale fields, including the radial `vulnerability_closure_mps` actually used by the effects model; these fields make vulnerability adjustment auditable but do not grant Pk or deterministic-fuze authority.
- Representative F-16, Su-35S, MQ-9, MH-60R, and E-3 target-family vulnerability scaffolds spawn as synthetic/non-authoritative evidence; the non-F-16 profiles are neutral scale placeholders and do not change uncalibrated damage strength.
- Calibrated vulnerability rows can drive family/aspect/closure/miss-distance/effect scales only when the descriptor passes the evidence gate and explicitly grants `effect_scale_authority`; component-failure probability rows likewise require `component_failure_probability_authority`; rows without the matching authority are ignored.
- The database-level F-16, Su-35S, MQ-9, MH-60R, and E-3 examples now carry 20+ representative components. The fighter examples cover navigation, power-bus, IFF/IRST, thrust-vector, rudder, and leading-edge actuator attach points; the UAV/helicopter/C2 examples cover mission sensors, command/data links, mission processing, power generation/distribution, propulsion/transmission, fuel, control actuators, and structural spars. These examples distinguish component-specific consequences and author per-component `mechanism_thresholds` for blast, fragmentation, blast-fragmentation, continuous-rod, and hit-to-kill effects, while remaining engineering scaffolds rather than calibrated vulnerability data.
- Component `dependencies` can propagate control-actuator damage into hydraulic/flight-control overlays, mission-radar damage into avionics/mission-system overlays, and representative power/data-link damage into avionics, flight-control, data-link, and mission-system overlays across the current aircraft units; this remains a minimal dependency scaffold, not a complete dependency graph.
- Named control-component damage can derive axis-specific roll/pitch/yaw authority loss and control-asymmetry evidence for aileron/elevon/rudder/flap/thrust-vector/cyclic/collective components before any full flight-control torque-law rewrite.
- Vulnerability authority requires a loaded, non-synthetic, calibrated evidence descriptor that matches the target type and declares weapon/aspect/closure/miss-distance evidence axes; aircraft JSON self-claims, missing descriptors, synthetic placeholder descriptors, incomplete evidence axes, and per-authority descriptor denials keep Pk / deterministic-fuze authority disabled.
- `EffectsEvent` exposes fuze type, trigger radius, delay, reliability, and synthetic provenance as evidence; this does not release deterministic fuze authority.
- `EffectsEvent` exposes detonation heading/pitch/roll captured from live missile attitude at fuze arming, and the effects model derives target-body `warhead_orientation_axis_*` plus `warhead_orientation_pattern_scale` evidence from that attitude; this remains parameterized orientation evidence, not a calibrated orientation-driven fragment or rod effect model.
- `EffectsEvent` exposes proximity-fuze target-signature evidence (`fuze_signature_source`, `fuze_target_signature`, `fuze_signature_scale`, `fuze_effective_reliability`), so radar/laser proximity fuzes can start consuming target RCS/aspect or projected-geometry proxies without becoming calibrated deterministic fuzes.
- `EffectsEvent` exposes contact/impact-fuze surface distance, penetration depth, contact tolerance, and inside-hitbox evidence; this proves contact fuzes are not proximity-radius aliases, but it is still a geometry audit scaffold rather than a calibrated penetration/delay/failure model.
- `EffectsEvent.detonation_time_s` can be delayed after `nearest_approach_time_s` by `fuze_delay_s`; this remains a scheduled proximity-fuze effect, not deterministic fuze release.
- Contact/impact fuze profiles do not trigger merely because a missile enters the proximity radius; they require near-surface contact against target hitbox geometry.
- Timed fuze profiles can detonate by launch-time delay without entering the proximity gate; physical damage still depends on detonation geometry and warhead footprint.
- Different hitboxes produce different capability consequences.
- HP is a derived compatibility readout.
- Reward/score layers consume damage reports and kill state without writing back into physical effects authority.
- Nonterminal structured damage can provide RL shaping through a consumer-side `DamageReport` surface and cannot be scored repeatedly from the same report id.
- Legacy smoke remains compatible but tests distinguish legacy HP path from structured damage path.
- Stage 0 fixed-fire smoke validates weapon-release reachability and stability only; because deterministic fuze remains deferred, a single live missile inside fuse radius is not a guaranteed `combat_win`.
- Because proximity fuze resolution happens after nearest approach, `closure_mps` may be zero at event time and must be treated as diagnostic evidence, not deterministic-fuze authority.

Focused evidence:

```bash
source tools/maintenance/cmo_env.sh && cmo_python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py::AirCombat1v1FireMissileTests::test_fired_missile_does_not_retarget_friendly_and_records_engagement \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_live_missile_hit_records_structured_air_damage_without_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_target_uses_damage_state_instead_of_hp_first_kill \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_structured_air_damage_does_not_write_rl_score_from_physical_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_e3_sentry_c2node_uses_authored_structured_damage_model \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_aircraft_database_units_have_authored_structured_damage_models \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_definition_missile_tuning_flows_into_launch_runtime \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_global_warhead_profile_override_flows_into_runtime_and_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_fuze_event_records_detonation_attitude_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_family_changes_structured_air_effect_distribution \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_proximity_field_projects_near_miss_onto_nearest_air_hitbox \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_spatial_projection_respects_warhead_family_footprint \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_continuous_rod_near_miss_uses_relative_velocity_axis \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_orientation_axis_modulates_rod_pattern_evidence \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_database_f16_component_geometry_reports_primary_component \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_database_su35_component_geometry_reports_primary_component \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_representative_aircraft_database_components_cover_uav_helo_c2 \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_representative_aircraft_components_report_runtime_identity \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_dependencies_are_authored_for_representative_control_and_mission_components \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_mission_component_dependency_damage_propagates_to_avionics_overlay \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase3_component_redundancy_reduces_failure_probability \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_aircraft_vulnerability_profile_modulates_structured_damage \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_vulnerability_adjustment_is_recorded_on_effects_event \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_vulnerability_claim_requires_dataset_descriptor \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_synthetic_descriptor_cannot_grant_vulnerability_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_grants_only_requested_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_requires_evidence_axes \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_calibrated_descriptor_can_grant_pk_and_deterministic_fuze_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_vulnerability_rows_drive_effects_event_scales \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_vulnerability_rows_require_effect_scale_authority \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_authorized_rows_drive_component_failure_probability \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase5_component_failure_rows_require_probability_authority \
  tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py \
  tests/runtime/air_combat/test_weapon_guidance_realism_guards.py::WeaponGuidanceRealismGuardTests::test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries
```

Recent focused result for the latest air-combat increment: `cmake --build build-local-win --target ef_py --config Release -j 4` passed; the focused contract/binding/component-load subset passed with `26 passed`; the air-combat guard + evidence descriptor subset passed with `92 passed, 87 subtests passed`; the engagement/binding contract subset passed with `52 passed`; `git diff --check` passed.

## External Review

- [高保真要求独立评审](review_high_fidelity_requirements_20260526.zh.md) — 从空战杀伤建模领域要求出发，定义高保真的实质标准，独立于项目自身文档。

## Task Cluster

- [High-fidelity damage model cluster](high_fidelity_damage_model_cluster_20260526.zh.md)
