# Kill-Chain Metric Mapping

Status: `2026-06-23` P3 pass metric mapping for
[Kill-Chain Expectation Standardization](README.md). This is a docs-only field
contract; it does not run simulation, retune runtime parameters, edit
descriptors, or claim real AIM-120C/F-16C/Pk authority.

Chinese companion:
[kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md)

Schema label: `a2.kill_chain_metric_mapping.v0`

## Inputs

- P1 contract:
  [kill_chain_idealized_expectation_contract_20260621.md](kill_chain_idealized_expectation_contract_20260621.md)
- P2 scenario matrix:
  [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md)
- Current decoupled diagnostics surface:
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)
- Current lethality abstraction:
  [lethality_abstraction.py](../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_abstraction.py)
- Current scalar ledger:
  [lethality_scalar_ledger.py](../../../../../tools/diagnostics/_air_combat_weapon_employment_process_probe_impl/lethality_scalar_ledger.py)
- Current runtime contract fields:
  [engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)

## P3 Boundary

P3 only answers which report fields each heatmap cell should read or derive. It
does not answer:

- meter-valued `R_fuze` or `R_effect` calibration;
- component-failure probability thresholds;
- real weapon or real target authority;
- Pk, reward, or entity-deletion authority;
- whether runtime parameters should change.

Field availability uses these labels:

| Label | Meaning |
| --- | --- |
| `runtime-current` | Current runtime facade or engagement events can export the field directly. |
| `diagnostic-current` | Current diagnostics can export the field from chain rows / scalar ledger. |
| `derived-report` | P3/P4 reports can derive the field from declared profile data and runtime facts. |
| `planned-harness` | The P4 harness must provide it as input metadata or a new report column. |
| `held-authority` | Requires a future admission gate; P3 must not use it as calibration authority. |

## Stage Metric Map

| Metric id | Stage / owner | Fields | Source | Use | Availability |
| --- | --- | --- | --- | --- | --- |
| `KCES-M0` | `launch_window` / harness metadata | `profile_id`, `grid_tier`, `case_id`, `target_motion_layer`, `range_km`, `offset_deg`, `signed_bearing_deg`, `seed`, `launch_class` | P2 heatmap and P4 case generator; the current guidance probe already has `case_id`, `range_m`, `bearing_deg`, `seed` | Group heatmap cells and carry the `N/M/O` expectation class. | `planned-harness` + partial `runtime-current` |
| `KCES-M1` | `guidance_approach` / `approach` | `nearest_distance_m`, `nearest_approach_time_s`, `truth_min_distance_m`, `closest_point_local_forward_m`, `closest_point_local_right_m`, `closest_point_local_up_m`, `closure_mps`, `max_achieved_lateral_g` | `guidance_cases[].nearest_miss_distance_m`, `truth_min_distance_m`, `max_achieved_lateral_g`, `runtime_facade.approach_fact.*`, `lethality_chain_stage_abstractions[].observed.*` | Judge `R_fuze` entry and separate guidance / kinematic issues from lethality issues. | `runtime-current` / `diagnostic-current` |
| `KCES-M2` | `guidance_approach` / `approach` | `R_fuze_m`, `rho_fuze`, `entered_R_fuze`, `guidance_expectation_status` | `R_fuze_m` comes from the profile-declared proxy; `rho_fuze = nearest_distance_m / R_fuze_m` | Convert `N/M/O` expectations into normalized guidance metrics. | `derived-report`; `R_fuze_m` is `planned-harness` until declared |
| `KCES-M3` | `fuze_decision` | `fuze_triggered`, `fuze_reason`, `detonated`, `outcome_state`, `detonation_probability`, `fuze_quality`, `sensor_opportunity_score`, `terminal_track_valid`, `target_detected`, `target_detection_confidence`, `target_detection_threshold`, `detonation_point_source`, `trigger_radius_m` | `guidance_cases[].fuze_*`, `runtime_facade.fuze_decision.*`, `lethality_chain_stage_abstractions[].observed.*` | Explain whether an entered `R_fuze` resulted in a trigger; does not grant deterministic-fuze authority. | `runtime-current` / `diagnostic-current` |
| `KCES-M4` | `warhead_load_field` | `R_effect_variant`, `R_effect_m`, `rho_effect_case`, `rho_effect_component`, `effect_band`, `effect_family`, `lethal_radius_m`, `spatial_effect_scale`, `mechanism_effect_scale`, `fragment_energy_j`, `fragment_areal_density_per_m2`, `penetration_margin`, `blast_overpressure_kpa`, `blast_impulse_kpa_ms`, `blast_scaled_distance_m_kg13`, `rod_cut_margin`, `surface_incidence_cos` | `runtime_facade.warhead_load_field.*`, `component_loads[]`, P3 variant rules | Separate post-fuze load from guidance / fuze success and support `REV-*` sensitivity rows. | `runtime-current` + `derived-report` |
| `KCES-M5` | `warhead_load_field` / component load rows | `component_name`, `component_system`, `component_redundancy_group_id`, `component_distance_m`, `component_effect_scale`, `spatial_intersection_fraction`, `pattern_weight`, `orientation_weight`, `receiver_exposure_fraction`, `armor_transmission`, `sampling_confidence`, `load_intensity_scale` | `runtime_facade.warhead_load_field.component_loads[]` | Explain component-level reasons for strong or weak load after a trigger. | `runtime-current` |
| `KCES-M6` | `component_response` | `component_response_row_count`, `failure_probability`, `failure_sample`, `failure_mode`, `failure_severity`, `integrity_before`, `integrity_after`, `integrity_delta`, `component_response_band`, `sampled_failure` | `runtime_facade.component_responses[]`, `runtime_facade.component_response.*`, component-response abstraction | Evaluate target response only after fuze/load success; never compensate for a miss outside `R_fuze`. | `runtime-current` + `derived-report` |
| `KCES-M7` | `consequence_projection` | `outcome_state`, `component_hit_count`, `component_failure_count`, `primary_component_name`, `primary_component_system`, `primary_component_integrity`, `redundancy_group_availability`, `air_system_hit_flags`, `air_system_spatial_scales`, `vulnerability_scale_trace`, `mission_kill`, `mobility_kill`, `sensor_kill`, `destroyed` | `runtime_facade.consequence_projection.*`, consequence abstraction | Downstream observation only; never back-infer guidance / fuze / load expectations. | `runtime-current` / `diagnostic-current` |
| `KCES-M8` | owner guard / scalar ledger | `scalar_id`, `current_owner_stage`, `intended_owner_stage`, `producer_stage`, `producer_field`, `consumer_fields`, `coupling_flags`, `calibration_ready` | `lethality_chain_scalar_ledger`, `lethality_chain_scalar_coupling_summary` | P4 single-layer calibration guard; confirms that only one layer changes at a time. | `diagnostic-current` |

## Derived Field Rules

`nearest_distance_m` read priority:

```text
nearest_distance_m =
  guidance_cases[].nearest_miss_distance_m
  or runtime_facade.approach_fact.closest_distance_m
  or guidance_cases[].truth_min_distance_m
```

`rho_fuze`:

```text
rho_fuze = nearest_distance_m / R_fuze_m
entered_R_fuze = rho_fuze <= 1.0
```

P3 does not choose `R_fuze_m`. The P4 harness must explicitly declare the
profile source for `R_fuze_m`; if it references the current repository proxy
trigger radius, it must label it as engineering proxy.

`rho_effect` has two levels:

```text
rho_effect_case = nearest_distance_m / R_effect_m
rho_effect_component = component_loads[].distance_m / R_effect_m
```

`rho_effect_case` supports heatmap overview; `rho_effect_component` supports
component-level response explanation. When component load rows are available,
P4 reports should prefer `rho_effect_component` for `component_response`
interpretation.

`effect_band` uses the P1 qualitative bands:

| Condition | `effect_band` |
| --- | --- |
| `rho_effect <= 0.25` | `core` |
| `0.25 < rho_effect <= 0.50` | `effective` |
| `0.50 < rho_effect <= 0.80` | `outer_effective` |
| `0.80 < rho_effect <= 1.00` | `edge` |
| `rho_effect > 1.00` | `outside_effect` |
| `R_effect_m` undeclared | `unclassified_missing_R_effect` |

`component_response_band` is not quantified in P3. P3 only requires the report
to carry `failure_probability`, `failure_sample`, `sampled_failure`,
`integrity_delta`, `failure_mode`, and `failure_severity`. Probability and
integrity thresholds move to P4 or follow-on admission work.

## R Effect Variant Mapping

| Variant id | `R_effect_m` source | P3 status | Report requirement |
| --- | --- | --- | --- |
| `REV-RUNTIME-PROJECTION` | Current runtime projection proxy. Prefer `runtime_facade.warhead_load_field.lethal_radius_m`; if absent, P4 must provide `runtime_projection_radius_m`. | selected | Label `authority_level=runtime_projection_comparison`; not an idealized standard. |
| `REV-EQ-FUZE` | `R_effect_m = R_fuze_m`. | selected | Sensitivity upper bound; reports must set `derived_from_fuze_radius=true`. |
| `REV-SMALLER-LOAD` | P4 harness-declared `declared_effect_radius_m`, which must be `< R_fuze_m`. | selected but value-held | No default meter value; if absent, output `unclassified_missing_R_effect`. |
| `REV-DECLARED-EFFECT` | Future review/admitted evidence row. | held | Not part of the current P3/P4 default calibration. |

`R_effect_variant` is normally an offline evaluation dimension. Unless P4 proves
that runtime re-execution is required, `REV-*` should not multiply simulation
case count.

## Heatmap Report Row Schema

Each P4 heatmap report row should include at least:

| Field group | Required fields |
| --- | --- |
| `identity` | `schema_version`, `profile_id`, `case_id`, `grid_tier`, `sample_index`, `seed` |
| `launch_window` | `target_motion_layer`, `range_km`, `offset_deg`, `signed_bearing_deg`, `launch_class` |
| `guidance_approach` | `nearest_distance_m`, `nearest_approach_time_s`, `closure_mps`, `max_achieved_lateral_g`, `R_fuze_m`, `rho_fuze`, `entered_R_fuze`, `guidance_expectation_status` |
| `fuze_decision` | `fuze_triggered`, `fuze_reason`, `detonated`, `detonation_probability`, `fuze_quality`, `terminal_track_valid`, `target_detected`, `detonation_point_source` |
| `warhead_load_field` | `R_effect_variant`, `R_effect_m`, `rho_effect_case`, `effect_band`, `component_load_row_count`, `strongest_component_effect_scale`, `weakest_component_effect_scale` |
| `component_response` | `component_response_row_count`, `max_failure_probability`, `sampled_failure_count`, `min_integrity_delta`, `primary_failure_mode`, `component_response_band` |
| `consequence_projection` | `outcome_state`, `component_hit_count`, `component_failure_count`, `primary_component_system`, `mission_kill`, `mobility_kill`, `sensor_kill`, `destroyed` |
| `guards` | `scalar_owner_guard_status`, `unexpected_stage_delta`, `authority_boundary_status`, `runtime_parameter_retuning` |

Recommended `guidance_expectation_status`:

| `launch_class` | Condition | Status |
| --- | --- | --- |
| `N` | `entered_R_fuze=true` | `satisfied` |
| `N` | `entered_R_fuze=false` | `guidance_or_model_residual` |
| `M` | any outcome | `observed_marginal`, with stage facts retained |
| `O` | `entered_R_fuze=false` | `negative_control_satisfied` |
| `O` | `entered_R_fuze=true` or strong load / response appears | `negative_control_alert` |

Recommended `authority_boundary_status`:

| Condition | Status |
| --- | --- |
| `runtime_parameter_retuning=false` and `calibration_authority=false` and `real_world_pk=false` | `engineering_proxy_guarded` |
| Any field attempts to claim real weapon/target/Pk authority | `authority_violation` |

## Sampling Tier Mapping

| Sampling tier | P3 field requirement | P4 use |
| --- | --- | --- |
| `anchor-grid` | Must fully output all `KCES-M0` through `KCES-M8` fields; 1 seed is allowed. | Smoke and report schema validation. |
| `recommended-main-grid` | Must output the signed bearing heatmap and preserve grouping fields for each `N/M/O` cell. | First calibration heatmap and continuity check. |
| `boundary-refinement` | Must reference the original coarse cell and record `refinement_reason=N/M_boundary` or `M/O_boundary`. | Avoid coarse-grid misclassification. |
| `expanded-maneuver-grid` | Must record target maneuver profile id, maneuver severity, and target-acceleration summary. | Generality expansion after the maneuver layer matures. |

## P3 Closure

P3 is pass. It has:

- mapped P2 heatmap cells, sampling tiers, and `R_effect_variant` values to
  stage-report fields;
- separated `runtime-current`, `diagnostic-current`, `derived-report`,
  `planned-harness`, and `held-authority`;
- defined derivation rules for `rho_fuze`, `rho_effect_case`, and
  `rho_effect_component`;
- made `REV-SMALLER-LOAD` require an explicit P4 `declared_effect_radius_m`,
  with no default value;
- provided a heatmap report row schema and guard fields for P4.

P3 does not resolve:

- concrete parameter values;
- P4 harness CLI / parallel execution design;
- probability or integrity thresholds;
- standards promotion;
- real authority admission.

Those move to P4/P5 or future evidence work.
