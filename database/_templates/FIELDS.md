# Template Field Reference

Language: English canonical. Chinese companion: not established.

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_templates/FIELDS.md`
Owner: `database/equipment-data`
Last verified: `not established`
Content status: Draft field reference for provisional templates. It is not a final schema or runtime authority.

Machine-readable constraints are owned by `common.schema.json` and the matching type `*.schema.json`; this document explains field semantics and current caveats.

## General Fields

`_comment` is an inline hint retained from repository examples. It is not equipment data and must not be treated as a contract field.

| Template field | Type / unit | Meaning | Status |
| --- | --- | --- | --- |
| `name` | string | Stable unit lookup name used by runtime spawn and cross-file references. | Required in populated entries |
| `type` | string | Unit discriminator. Values must match the supported `UnitType` spelling. | Required |
| `_template` | boolean | Marks the file as a template rather than collected data. Used only in the source template. | Template-only |
| `_status` | string | Template or source-record status marker. | Template-only |

## Aircraft

Based on the repository aircraft examples. Units follow the field suffix unless stated otherwise.

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `airframe.empty_mass_kg` | kg | Aircraft empty mass. |
| `airframe.max_fuel_kg` | kg | Internal fuel capacity used by the current aircraft mass model. |
| `airframe.drag_coefficient` | dimensionless | Reference drag coefficient used by the simplified flight model. |
| `airframe.reference_area` | m^2 | Aerodynamic reference area. |
| `airframe.length_m` | m | Overall aircraft length. |
| `airframe.wingspan_m` | m | Wing span. |
| `airframe.height_m` | m | Overall aircraft height. |
| `airframe.configuration` | string | Procedural configuration label such as `Conventional`. |
| `health.current_hp`, `health.max_hp` | HP | Current and maximum platform health. |
| `damage_model.vulnerability.synthetic` | boolean | Declares whether vulnerability values are synthetic. |
| `damage_model.vulnerability.calibrated` | boolean | Declares whether vulnerability values are calibrated. |
| `damage_model.vulnerability.pk_authority` | boolean | Declares whether the entry has Pk authority. |
| `damage_model.vulnerability.deterministic_fuze_authority` | boolean | Declares whether the entry has deterministic-fuze authority. |
| `damage_model.vulnerability.provenance` | string | Short provenance note for vulnerability inputs. |
| `damage_model.vulnerability.evidence_dataset_ref` | reference | Evidence dataset reference. |
| `damage_model.vulnerability.calibration_status` | string | Calibration state such as `unvalidated`. |
| `damage_model.vulnerability.*_scale` | multiplier | Blast, fragmentation, continuous-rod, hit-to-kill, aspect, closure, near-miss, and direct-hit scaling inputs. |
| `damage_model.hitboxes[]` | array | Component or region geometry consumed by the damage model. Populate from an accepted damage definition rather than the template placeholder. |
| `flight_model.max_speed`, `min_speed` | m/s | Simplified speed envelope. |
| `flight_model.max_turn_rate` | deg/s | Maximum turn-rate limit. |
| `flight_model.max_climb_rate` | m/s | Maximum climb-rate limit. |
| `flight_model.max_accel` | m/s^2 or model-defined acceleration | Acceleration limit used by the current simplified model. |
| `flight_model.max_g`, `min_g` | g | Positive and negative load limits. |
| `landing_gear.can_use_unpaved` | boolean | Whether unpaved surfaces are allowed. |
| `landing_gear.rolling_friction_coeff` | dimensionless | Ground rolling-friction coefficient. |
| `landing_gear.max_load_factor` | g | Landing-gear load limit. |
| `landing_gear.contact_height_m` | m | Gear contact height above the platform reference point. |
| `engine_ref` | string reference | Name of an `Engine` definition. |
| `sensor_ref`, `sensor_refs[]` | string reference(s) | Name of one or more `Sensor` definitions. |
| `ew_suite_ref` | string reference | Intended `EWSuite` reference. The current loader recognizes the key but does not populate it; do not rely on it until explicitly repaired. |
| `rcs_profile_ref` | string reference | Intended `RCSProfile` reference. The current loader recognizes the key but does not populate it; do not rely on it until explicitly repaired. |
| `has_data_link` | boolean | Enables the data-link component for the platform. |
| `data_link_network_id` | integer | Network identifier present in examples. Current materialization may assign network identity by side rather than consume this value. |
| `hardpoints[].station_id` | integer | Station identifier used by `default_loadout`. |
| `hardpoints[].type[]` | string list | Supported station or launcher classes. |
| `hardpoints[].capacity_kg` | kg | Station carrying capacity. |
| `default_loadout` | object | Maps stringified station IDs to weapon definition names. |
| `has_ammo` | boolean | Enables the generic ammo component where applicable. |
| `_provenance.sources[]` | reference list | Source references used by the entry. |
| `_provenance.modeling_notes[]` | string list | Modeling assumptions and non-authoritative boundaries. |

## Ship

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `ship_platform.displacement_light_kg`, `.displacement_full_load_kg` | kg | Light and full-load displacement. |
| `ship_platform.length_m`, `.beam_m`, `.draft_m` | m | Hull dimensions. |
| `ship_platform.height_above_waterline_m` | m | Estimate used for line-of-sight and radar-horizon calculations. |
| `ship_platform.max_speed_mps`, `.economical_speed_mps` | m/s | Maximum and economical speeds. |
| `ship_platform.range_nm`, `.range_speed_mps` | nmi, m/s | Range and the speed at which it is quoted. |
| `ship_platform.max_accel_mps2`, `.max_decel_mps2` | m/s^2 | Accel/decel limits. |
| `ship_platform.max_turn_rate_deg_s` | deg/s | Maximum turn-rate limit. |
| `ship_platform.low_speed_turn_factor` | multiplier | Turn-rate reduction at low speed. |
| `ship_platform.steerageway_speed_mps` | m/s | Minimum speed for effective steering. |
| `ship_platform.sea_state`, `.wave_heading_deg`, `.wave_period_s` | state, deg, s | Sea-state and wave inputs. |
| `ship_platform.max_roll_deg_sea_state_6`, `.max_pitch_deg_sea_state_6` | deg | Roll and pitch response at sea state 6. |
| `ship_platform.added_resistance_fraction_sea_state_6` | fraction | Added resistance at sea state 6. |
| `ship_platform.crew` | persons | Crew count. |
| `sensor_ref`, `sensor_refs[]` | reference(s) | Ship sensor definitions. |
| `esm.sensitivity_dbm`, `.max_detection_range_m`, `.classify_emitters` | dBm, m, boolean | Passive ESM sensitivity, detection range, and classification behavior. |
| `command_link.latency_s`, `.drop_prob` | s, probability | Command-link latency and loss probability. |
| `data_link_network_id` | integer | Example network identifier; current materialization may overwrite it. |
| `naval_stores.*_current`, `*_max` | abstract units | Current and maximum fuel, missile, and dry-cargo store levels. |
| `naval_stores.can_receive_underway`, `.can_provide_underway` | boolean | Enables underway replenishment receive/provide behavior. |
| `naval_weapon_system.mounts[]` | array | Weapon mounts. Mount fields are documented in the referenced DDG-51 example and must not be inferred from this placeholder. |
| `damage_model.hitboxes[]` | array | Ship hitbox/component geometry. |
| `_real_world` | object | Public identity and equipment notes. Not runtime authority by itself. |
| `_provenance.unit_conversions[]`, `.sources[]`, `.modeling_notes[]` | lists | Unit conversions, source references, and modeling boundaries. |

## Submarine

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `submarine_platform.submerged_displacement_kg` | kg | Submerged displacement. |
| `submarine_platform.length_m`, `.beam_m`, `.draft_m` | m | Hull dimensions. |
| `submarine_platform.max_speed_submerged_mps`, `.quiet_speed_mps` | m/s | Maximum submerged speed and quiet speed. |
| `submarine_platform.max_accel_mps2`, `.max_decel_mps2` | m/s^2 | Accel/decel limits. |
| `submarine_platform.max_turn_rate_deg_s`, `.max_depth_rate_mps` | deg/s, m/s | Turn-rate and depth-rate limits. |
| `submarine_platform.nominal_patrol_depth_m`, `.max_operating_depth_m` | m | Nominal patrol and maximum operating depths. |
| `submarine_platform.acoustic_stealth_bias_db`, `.self_noise_per_speed_db` | dB | Acoustic stealth bias and speed-dependent self noise. |
| `submarine_platform.crew` | persons | Crew count. |
| `mounted_sonars[].label` | string | Sonar mount label. |
| `mounted_sonars[].sonar.mode` | string | Sonar mode such as passive or active. |
| `sonar.max_range_m`, `.scan_period_s`, `.track_memory_s` | m, s, s | Detection range, scan cadence, and track retention. |
| `sonar.detection_threshold_db`, `.directivity_gain_db`, `.ambient_noise_db` | dB | Detection and acoustic terms. |
| `sonar.bearing_noise_std_deg`, `.range_noise_std_m` | deg, m | Measurement noise. |
| `sonar.source_level_reference_db`, `.source_level_speed_factor_db`, `.transmission_loss_alpha_db_per_km` | dB, dB, dB/km | Source-level and propagation terms. |
| `sonar.layer_break_penalty_db`, `.baffle_exclusion_deg` | dB, deg | Propagation and baffle constraints. |
| `sonar.self_noise_per_speed_db`, `.ownship_quieting_speed_mps` | dB, m/s | Own-ship noise and quieting behavior. |
| `sonar.confirm_hits_m`, `.confirm_window_n` | count | Track-confirmation thresholds. |
| `sonar.passive_only`, `.bearing_only` | boolean | Sonar operating constraints. |
| `command_link.latency_s`, `.drop_prob` | s, probability | Command-link behavior. |
| `_provenance.sources[]`, `.modeling_notes[]` | lists | Source references and modeling boundaries. |

## Ground

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `mass_kg` | kg | Ground-unit mass placeholder. |
| `health.current_hp`, `.max_hp` | HP | Unit health. |
| `has_score`, `has_command_link`, `has_data_link` | boolean | Optional runtime capability flags. |
| `command_link.latency_s`, `.drop_prob` | s, probability | Command-link behavior. |
| `_ground_schema.specialization` | string | Ground specialization label. |
| `_ground_schema.service_profile` | string | Service profile such as `Army`. |
| `_ground_schema.tasking_profile` | string | Tasking profile label. |
| `_ground_schema.tactical_unit_type` | string | Tactical unit category. |
| `_ground_schema.echelon` | string | Unit echelon such as platoon. |
| `_ground_schema.platform_family` | string | Declared platform family. |
| `_ground_schema.doctrine_family` | string | Doctrine family. |
| `_ground_schema.mobility_declaration` | string | Declared mobility state. |
| `_ground_schema.movement_behavior` | string | Declared movement behavior boundary. |
| `_deferred_runtime_claims[]` | string list | Behaviors intentionally not claimed by the ground fixture. |

## Facility

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `health.current_hp`, `.max_hp` | HP | Facility health. |
| `sensor.max_range`, `.fov_deg` | m, deg | Facility sensor range and field of view. |
| `has_data_link` | boolean | Enables the data-link component. |
| `damage_model.hitboxes[].id` | integer | Hitbox identifier. |
| `hitboxes[].size[]` | m | Hitbox dimensions. |
| `hitboxes[].armor` | model-defined | Armor input. |
| `hitboxes[].systems[]` | string list | Systems covered by that hitbox. |

## Modules

### Engine

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `engine.mil_thrust_n`, `.ab_thrust_n` | N | Military and afterburner thrust. |
| `engine.sfc_mil`, `.sfc_ab` | model-defined | Specific fuel consumption in military and afterburner modes. |
| `engine.bypass_ratio` | ratio | Engine bypass ratio. |

### Sensor

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `max_range`, `fov_deg`, `scan_period` | m, deg, s | Detection range, field of view, and scan cadence. |
| `detection_prob`, `bearing_noise_std`, `range_noise_std` | probability, deg, m | Detection probability and measurement noise. |
| `track_memory_s`, `range_power`, `aspect_influence`, `doppler_notch_width` | s, model-defined, model-defined, model-defined | Track retention and simplified radar terms. |

### EW Suite

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `rwr.sensitivity_dbm`, `.detect_band`, `.library_generation`, `.is_active` | dBm, band, generation, boolean | RWR sensitivity, band coverage, library generation, and activation. |
| `jammer.power_watts`, `.bandwidth_mhz`, `.type`, `.effective_angle`, `.is_active` | W, MHz, string, deg, boolean | Jammer output, bandwidth, mode, effective angle, and activation. |
| `countermeasures.chaff_count`, `.flare_count`, `.release_interval`, `.auto_mode` | count, count, s, boolean | Countermeasure inventory and release behavior. |

### RCS Profile

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `rcs.frontal_rcs`, `.side_rcs`, `.rear_rcs`, `.top_rcs`, `.bottom_rcs` | m^2 or model-defined | Aspect-dependent radar cross-section inputs. |

## Missile

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `mass_kg` | kg | Missile mass. |
| `max_flight_time_s` | s | Maximum flight time. |
| `flight_model.max_speed`, `.max_g`, `.max_turn_rate` | m/s, g, deg/s | Simplified flight envelope. |
| `guidance.type`, `.active_seek_range`, `.nav_gain`, `.apn_target_accel_gain` | string, m, gain, gain | Guidance mode and guidance-law parameters. |
| `guidance.autopilot_tau_s`, `.max_accel_response_g_per_s` | s, g/s | Autopilot response terms. |
| `warhead.type`, `.mass_kg`, `.lethal_radius`, `.damage` | string, kg, m, model-defined | Warhead classification, mass, radius, and damage input. |
| `warhead.explosive_mass_kg`, `.case_mass_kg` | kg | Explosive and case masses. |
| `warhead.projection_radius_fraction`, `.projection_max_radius_m`, `.projection_max_projected_hitboxes` | fraction, m, count | Projection approximation controls. |
| `warhead.provenance`, `fuze.provenance` | string | Source and authority boundary for warhead/fuze inputs. |
| `fuze.type`, `.trigger_radius_m`, `.delay_s`, `.reliability` | string, m, s, probability | Fuze type and behavior. |

## Source Ledger

| Field | Type | Meaning |
| --- | --- | --- |
| `source_id` | string | Stable identifier used by model-data references. |
| `source_tier` | string | Admission tier such as Tier A, B, or C. |
| `source_category` | string | Source category. |
| `source_ref` | string | Stable locator such as DOI, URL, report number, commit, or manifest. |
| `publisher_or_holder` | string | Publishing or holding organization. |
| `rights_or_redistribution` | string | License, copyright, export, or redistribution boundary. |
| `provenance_summary` | string | How the source was obtained, processed, and bounded. |
| `scope` | object | Supported target, platform, weapon, mechanism, terrain, or role scope. |
| `cross_validation[]` | list | Independent corroboration or sanity-check records. |
| `reasonableness_assessment` | string | Unit, range, consistency, and conflict assessment. |
| `ingest_status` | string | `pending`, `acquired`, `rejected`, or `superseded`. |
| `authority_status` | string | Authority state; defaults to `non-authoritative`. |
| `residuals[]` | list | Unresolved risks or evidence gaps. |

## Current Runtime Caveats

- `ew_suite_ref` and `rcs_profile_ref` exist in repository examples but are not populated by the current unit loader. They must not be treated as an effective reference path without an explicit contract repair.
- The final field set, required/optional policy, default behavior, and reference-resolution timing remain unresolved.
- Values copied into a template are placeholders, not calibrated data.
- Comments do not grant authority. Source-ledger, scope, rights, calibration, and validation rules remain separate requirements.
