# T11 Content Escape-Hatch Schema Survey (2026-07-21)

Language:
- English canonical: `t11_content_schema_survey_20260721.md`
- Chinese companion: [t11_content_schema_survey_20260721.zh.md](t11_content_schema_survey_20260721.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t11_content_schema_survey_20260721.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `1d25c4d1`

Status: T11 second-slice content escape-hatch schema survey for the
[Unified Architecture Program](README.md), executing step 2 of the slice order
in the census section 3 ("Content escape-hatch schema survey (docs + schema
draft; no parse change)"). It formalizes the **106** recognized content
top-level keys of face (i) — **54** read directly in `parse_unit_json` plus
**52** read by `parse_missile_tuning_json_fields` on the whole top-level entry —
across all **27** definition files, reusing the T1 `dto_schema` codec
escape-hatch precedent. This document is a descriptive census register
(`reference`), not an independent review: it records the verified baseline and
carries no review verdict. It changes no behavior and no `src/**` / `python/**`
/ `examples/config/**` code; it accompanies a machine-readable schema **draft**
(`tools/maintenance/dto_schema/drafts/content_unit_schema_draft.json`) that is
deliberately **not wired** into the generator (section 4). It builds on the
[T11 Content Compilation Pipeline Census (2026-07-21)](t11_content_pipeline_census_20260721.md)
and stays inside that census's section 3 red lines (reproduced in section 6).

## 0. Method And Scope

- **Key extraction.** Every `entry.value(...)`, `entry.contains(...)`, and
  `entry[...]` access site in `src/content/unit_definition_loader.cpp` was
  enumerated by regex and then verified line-by-line against the source at
  baseline `1d25c4d1`. `parse_unit_json` (`:804-1585`) accesses **54** distinct
  top-level keys on its `entry` argument. For a `Missile`-type unit it also
  routes the *entire* `entry` through `parse_missile_tuning_json_fields`
  (`:350-427`, invoked at `:1450`), which reads **52** further distinct
  top-level keys disjoint from the 54, for a semantic total of **106** keys.
  The 54/52 split and the 106 total match the census section 1(i) exactly
  (independently re-derived here; the disjointness was checked programmatically
  — the two key sets share no member). Cited read lines follow the
  **call-line convention**: a multi-line statement is cited at the line
  carrying the actual `.value(...)` / `parse_vector(...)` call with the quoted
  key literal, not at the assignment's opening line.
- **Distribution.** Each of the **27** definition files under
  `examples/config/database` (excluding the 2 `damage/vulnerability_evidence`
  descriptors, which load through a separate descriptor path) was parsed and its
  top-level keys and JSON value types recorded. Counts: **11** unit-platform,
  **12** module, **3** weapon, **1** facility. The "Files [U/M/W/F]" column of
  each table reports total files carrying the key at top level, split by
  category (U = unit-platform, M = module, W = weapon, F = facility).
- **Target structs.** `UnitDefinition` has **58** direct members
  (`unit_definition.h:177-265`); `MissileTuningDefinition` has **56** fields
  (`unit_definition.h:63-122`). Each key row maps to its member with a
  `file:line` decl reference.
- **Recognized vs exercised.** A `Files` value of `0` means the parser
  recognizes the key but no current definition file carries it at top level
  (a recognized-but-unused compatibility surface — expected for the flat
  escape-hatch forms and most missile-tuning scalars). This is a data-coverage
  fact, not a parse gap.
- **Auditability.** The per-key and orphan-key table bodies (sections 1 and 3)
  are byte-identical between this file and its Chinese companion; only the
  header rows and the section-5 verdict prose are translated. Zero behavior
  change; no `src/**` edit; no test edit.

## 1. Per-Key Specification Tables

Family and sentinel codes are terse; their full definitions live in the schema
draft's `escape_hatch_families` and `sentinel_legend` objects. Short legend:

- **Family** — `REQ` required discriminant · `ID` identity · `MASS` scalar mass
  · `REF` component ref string · `ENG` engine flat-or-nested dual · `LOAD`
  hardpoints/loadout · `HP` health · `SEN` sensor: `sensor_ref` independent if
  + refs/inline/flag three-way chain · `SON` sonar · `FLT` flight model · `LG`
  landing gear · `SCORE` score ·
  `AERO` airframe/aero_tuning dual · `NAV` naval platform blocks · `DMG` damage
  model (polymorphic `dependencies[]`, dual-form `failure_modes`, nested/flat
  geometry) · `AMMO` ammo · `MSL` missile-tuning triple-source merge · `WAR`
  warhead · `FUZ` fuze/fuse dual spelling + nested radius/logic aliases · `EW`
  EW blocks · `CMD` command link · `DL` data link scalars.
- **Default / sentinel** — `REQ` required · `type_str` optional, falls back to
  the `type` string · `0` numeric zero · `16`/`1`/`-1` int defaults/sentinels ·
  `true`/`false` bool defaults · `NaN` `quiet_NaN` unset marker · `FLAG` `has_*`
  presence flag · `{}` struct value-init / zero literal (no named preset) ·
  `PRESET` merged over a named codec preset (section 2) · `{100}` loader-literal
  health `{100,100}` (`:875`) · `[]` empty container/no-op · `unset` empty
  string / prior value.

### 1.1 Direct Top-Level Keys (54) — `parse_unit_json`

| # | Key | JSON type | Target member (`unit_definition.h`) | Read (`unit_definition_loader.cpp`) | Default / sentinel | Family | Forms / aliases | Files [U/M/W/F] |
|---:|-----|-----------|-------------------------------------|-------------------------------------|--------------------|--------|-----------------|-----------------|
| 1 | `type` | string | `UnitDefinition::type` (unit_definition.h:178) | `807,812` | `REQ` | REQ | discriminant | 27 [U11 M12 W3 F1] |
| 2 | `name` | string | `UnitDefinition::name` (unit_definition.h:179) | `818` | `type_str` | ID | optional: falls back to the type string (:818); single-object load_file path gates on presence (:1617) but the units[] path does not | 27 [U11 M12 W3 F1] |
| 3 | `mass_kg` | number | `UnitDefinition::mass_kg` (unit_definition.h:250) | `819` | `0` | MASS | - | 4 [U1 W3] |
| 4 | `engine_ref` | string | `UnitDefinition::engine_ref` (unit_definition.h:184) | `825,826` | `unset` | REF | unchecked get<string> | 2 [U2] |
| 5 | `engine` | object | `UnitDefinition::engine_data` (unit_definition.h:193) | `829,830` | `{}` | ENG | nested form; nested tuning -> default_engine_tuning() preset (:836-839) | 2 [M2] |
| 6 | `mil_thrust_n` | number | `UnitDefinition::engine_data.mil_thrust_n` (unit_definition.h:193) | `842` | `0` | ENG | flat form | 0 |
| 7 | `ab_thrust_n` | number | `UnitDefinition::engine_data.ab_thrust_n` (unit_definition.h:193) | `843` | `0` | ENG | flat form | 0 |
| 8 | `sfc_mil` | number | `UnitDefinition::engine_data.sfc_mil` (unit_definition.h:193) | `844` | `0` | ENG | flat form | 0 |
| 9 | `sfc_ab` | number | `UnitDefinition::engine_data.sfc_ab` (unit_definition.h:193) | `845` | `0` | ENG | flat form | 0 |
| 10 | `bypass_ratio` | number | `UnitDefinition::engine_data.bypass_ratio` (unit_definition.h:193) | `846` | `0` | ENG | flat form | 0 |
| 11 | `engine_tuning` | object | `UnitDefinition::engine_data.tuning` (unit_definition.h:193) | `847,852` | `PRESET` | ENG | alias of engine.tuning; default_engine_tuning() preset-then-merge (:848-852) | 0 |
| 12 | `hardpoints` | array | `UnitDefinition::hardpoints` (unit_definition.h:189) | `855,856` | `[]` | LOAD | - | 2 [U2] |
| 13 | `default_loadout` | object | `UnitDefinition::default_loadout` (unit_definition.h:190) | `869,870` | `[]` | LOAD | int-key map; std::stoi(key); COMMA-BLOCKER | 2 [U2] |
| 14 | `health` | object | `UnitDefinition::health` (unit_definition.h:230) | `876,877` | `{100}` | HP | - | 11 [U10 F1] |
| 15 | `sensor_ref` | string | `UnitDefinition::sensor_ref` (unit_definition.h:182) | `889,890` | `unset` | SEN | independent if (:889-893), can coexist with the chain; unchecked get<string> | 5 [U5] |
| 16 | `sensor_refs` | array | `UnitDefinition::sensor_refs` (unit_definition.h:183) | `894,895` | `[]` | SEN | three-way chain head (if, :894) | 2 [U2] |
| 17 | `sensor` | object | `UnitDefinition::sensor` (unit_definition.h:232) | `899,901;1490` | `PRESET+FLAG` | SEN | three-way chain else-if (:899); object form only; merges over make_unit_definition_default_sensor() 30 km preset (:883, missile re-preset :1491) | 8 [U1 M6 F1] |
| 18 | `has_sensor` | bool | `UnitDefinition::has_sensor` (unit_definition.h:231) | `905,906` | `FLAG` | SEN | three-way chain tail (else-if, :905) | 0 |
| 19 | `mounted_sensors` | array | `UnitDefinition::mounted_sensors` (unit_definition.h:233) | `909,910` | `[]` | SEN | per-mount make_unit_definition_default_sensor() preset (:914) | 1 [U1] |
| 20 | `sonar` | object | `UnitDefinition::sonar` (unit_definition.h:235) | `922,924` | `PRESET+FLAG` | SON | inline; merges over make_default_sonar_definition() 25 km preset (:886) | 1 [M1] |
| 21 | `mounted_sonars` | array | `UnitDefinition::mounted_sonars` (unit_definition.h:236) | `926,927` | `[]` | SON | per-mount make_default_sonar_definition() preset (:931) | 2 [U2] |
| 22 | `has_flight_model` | bool | `UnitDefinition::has_flight_model` (unit_definition.h:238) | `939` | `FLAG` | FLT | - | 0 |
| 23 | `flight_model` | object | `UnitDefinition::flight_model` (unit_definition.h:239) | `941,943` | `{}+FLAG` | FLT | in-block literals when key present: min_g -3.0 (:951), takeoff 80 / landing 70 / taxi 15 (:953-955) | 8 [U5 W3] |
| 24 | `has_landing_gear` | bool | `UnitDefinition::has_landing_gear` (unit_definition.h:243) | `958` | `FLAG` | LG | - | 0 |
| 25 | `landing_gear` | object | `UnitDefinition::landing_gear` (unit_definition.h:244) | `960,962` | `PRESET+FLAG` | LG | loader-literal paved-only preset {false,0.02,3.0,2.0,1.0,false,5.0} (:959) | 1 [U1] |
| 26 | `has_score` | bool | `UnitDefinition::has_score` (unit_definition.h:246) | `973` | `true` | SCORE | default true | 1 [U1] |
| 27 | `score` | object | `UnitDefinition::score` (unit_definition.h:247) | `975,976` | `{}` | SCORE | - | 0 |
| 28 | `airframe` | object | `UnitDefinition::airframe` (unit_definition.h:212) | `983,984` | `{}` | AERO | nested tuning -> default_aero_tuning() preset (:994-997) | 5 [U5] |
| 29 | `aero_tuning` | object | `UnitDefinition::airframe.tuning` (unit_definition.h:212) | `1000,1005` | `PRESET` | AERO | alias of airframe.tuning; default_aero_tuning() preset-then-merge (:1001-1005) | 0 |
| 30 | `stall_state` | object | `UnitDefinition::stall_state` (unit_definition.h:241) | `1007,1009` | `{}+FLAG` | AERO | - | 0 |
| 31 | `ship_platform` | object | `UnitDefinition::ship_platform` (unit_definition.h:214) | `1014,1016` | `{}+FLAG` | NAV | - | 4 [U4] |
| 32 | `submarine_platform` | object | `UnitDefinition::submarine_platform` (unit_definition.h:216) | `1060,1062` | `{}+FLAG` | NAV | - | 1 [U1] |
| 33 | `naval_stores` | object | `UnitDefinition::naval_stores` (unit_definition.h:218) | `1093,1095` | `{}+FLAG` | NAV | - | 2 [U2] |
| 34 | `naval_logistics` | object | `UnitDefinition::naval_logistics` (unit_definition.h:220) | `1116,1118` | `{}+FLAG` | NAV | - | 1 [U1] |
| 35 | `naval_weapon_system` | object | `UnitDefinition::naval_weapon_system` (unit_definition.h:222) | `1139,1140` | `{}+FLAG` | NAV | mounts[] required | 1 [U1] |
| 36 | `embarked_air_ops` | object | `UnitDefinition::embarked_air_ops` (unit_definition.h:224) | `1169,1171` | `{}+FLAG` | NAV | in-block enabled defaults true (:1184) | 1 [U1] |
| 37 | `damage_model` | object | `UnitDefinition::damage_model` (unit_definition.h:225) | `1189,1190` | `{}` | DMG | poly dependencies[]: string\|object (:1232-1254); failure_modes array\|object (:1305-1331) + failure_mode_weights overlay (:1332-1345); geometry nested-object\|flat-key dual path (:84-154, call :1351) with size/offset box fallback (:1352-1360) | 9 [U8 F1] |
| 38 | `has_ammo` | bool | `UnitDefinition::has_ammo` (unit_definition.h:252) | `1435` | `FLAG` | AMMO | - | 2 [U2] |
| 39 | `ammo` | object | `UnitDefinition::ammo` (unit_definition.h:253) | `1437,1439` | `{}+FLAG` | AMMO | - | 1 [U1] |
| 40 | `missile_tuning` | object | `UnitDefinition::missile_tuning` (unit_definition.h:264) | `1452,1453` | `{}` | MSL | merge source 2 (nested) | 0 |
| 41 | `guidance` | object | `UnitDefinition::missile_tuning` (unit_definition.h:264) | `1455,1456` | `{}` | MSL | merge source 3; alias active_seek_range,off_boresight_cap; type->seeker_type | 3 [W3] |
| 42 | `warhead` | object | `MissileTuningDefinition::warhead_profile` (unit_definition.h:118) | `1481,1482` | `{}+FLAG` | WAR | - | 3 [W3] |
| 43 | `fuze` | object | `MissileTuningDefinition::fuze_profile` (unit_definition.h:120) | `1484,1485` | `{}+FLAG` | FUZ | spelling A; radius alias trigger_radius_m\|trigger_radius\|radius_m (:476-482); trigger_logic\|trigger_mode fallback (:485-486) | 3 [W3] |
| 44 | `fuse` | object | `MissileTuningDefinition::fuze_profile` (unit_definition.h:120) | `1487,1488` | `{}+FLAG` | FUZ | spelling B (alias of fuze); same nested radius/logic aliases (:476-482, :485-486) | 0 |
| 45 | `has_command_link` | bool | `UnitDefinition::has_command_link` (unit_definition.h:255) | `1521` | `FLAG` | CMD | - | 9 [U9] |
| 46 | `command_link` | object | `UnitDefinition::command_link` (unit_definition.h:256) | `1523,1525` | `{}+FLAG` | CMD | - | 8 [U8] |
| 47 | `has_data_link` | bool | `UnitDefinition::has_data_link` (unit_definition.h:258) | `1530` | `FLAG` | DL | - | 11 [U10 F1] |
| 48 | `data_link_network_id` | int | `UnitDefinition::data_link_network_id` (unit_definition.h:259) | `1531` | `0` | DL | - | 8 [U8] |
| 49 | `data_link_max_reports_per_update` | int | `UnitDefinition::data_link_max_reports_per_update` (unit_definition.h:260) | `1533` | `16` | DL | max(0,x) | 0 |
| 50 | `data_link_max_messages_per_update` | int | `UnitDefinition::data_link_max_messages_per_update` (unit_definition.h:261) | `1535,1536` | `-1` | DL | falls back to reports value | 0 |
| 51 | `rwr` | object | `UnitDefinition::rwr_data` (unit_definition.h:203) | `1540,1541` | `{}` | EW | - | 1 [M1] |
| 52 | `jammer` | object | `UnitDefinition::jammer_data` (unit_definition.h:202) | `1545,1546` | `{}` | EW | - | 1 [M1] |
| 53 | `countermeasures` | object | `UnitDefinition::cms_data` (unit_definition.h:206) | `1563,1564` | `{}` | EW | member is cms_data | 1 [M1] |
| 54 | `esm` | object | `UnitDefinition::esm_data` (unit_definition.h:205) | `1574,1575` | `{}+FLAG` | EW | - | 1 [U1] |

### 1.2 Missile-Tuning Helper Keys (52) — `parse_missile_tuning_json_fields` On The Top-Level Entry

Read site is the helper line; `(@1450)` marks the call that passes the whole
top-level `entry`. The same helper is also invoked on nested `missile_tuning`
(`:1453`) and `guidance` (`:1457`); those are the same key names read nested,
not additional top-level keys.

| # | Key | JSON type | Target member (`unit_definition.h`) | Read (`unit_definition_loader.cpp`) | Default / sentinel | Family | Forms / aliases | Files [U/M/W/F] |
|---:|-----|-----------|-------------------------------------|-------------------------------------|--------------------|--------|-----------------|-----------------|
| 1 | `max_speed` | number | `MissileTuningDefinition::max_speed` (unit_definition.h:64) | `365 (@1450)` | `NaN` | MSL | seed=flight_model.max_speed | 0 |
| 2 | `turn_rate` | number | `MissileTuningDefinition::turn_rate` (unit_definition.h:65) | `366 (@1450)` | `NaN` | MSL | seed=flight_model.max_turn_rate | 0 |
| 3 | `fuse_distance` | number | `MissileTuningDefinition::fuse_distance` (unit_definition.h:66) | `367 (@1450)` | `NaN` | MSL | also set by warhead/fuze radius | 0 |
| 4 | `damage` | number | `MissileTuningDefinition::damage` (unit_definition.h:67) | `368 (@1450)` | `NaN` | MSL | also set by warhead | 0 |
| 5 | `seeker_fov_deg` | number | `MissileTuningDefinition::seeker_fov_deg` (unit_definition.h:68) | `369 (@1450)` | `NaN` | MSL | - | 0 |
| 6 | `seeker_lock_range` | number | `MissileTuningDefinition::seeker_lock_range` (unit_definition.h:69) | `370 (@1450)` | `NaN` | MSL | alias active_seek_range@guidance:1469 | 0 |
| 7 | `guidance_delay_s` | number | `MissileTuningDefinition::guidance_delay_s` (unit_definition.h:70) | `371 (@1450)` | `NaN` | MSL | - | 0 |
| 8 | `guidance_update_period_s` | number | `MissileTuningDefinition::guidance_update_period_s` (unit_definition.h:71) | `373 (@1450)` | `NaN` | MSL | - | 0 |
| 9 | `max_flight_time_s` | number | `MissileTuningDefinition::max_flight_time_s` (unit_definition.h:72) | `374 (@1450)` | `NaN` | MSL | - | 2 [W2] |
| 10 | `nav_gain` | number | `MissileTuningDefinition::nav_gain` (unit_definition.h:73) | `375 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 11 | `apn_target_accel_gain` | number | `MissileTuningDefinition::apn_target_accel_gain` (unit_definition.h:74) | `376 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 12 | `sensor_max_range` | number | `MissileTuningDefinition::sensor_max_range` (unit_definition.h:75) | `377 (@1450)` | `NaN` | MSL | alias@guidance:1471; entry.sensor.max_range | 0 |
| 13 | `sensor_fov_deg` | number | `MissileTuningDefinition::sensor_fov_deg` (unit_definition.h:76) | `378 (@1450)` | `NaN` | MSL | entry.sensor.fov_deg | 0 |
| 14 | `sensor_scan_period` | number | `MissileTuningDefinition::sensor_scan_period` (unit_definition.h:77) | `379 (@1450)` | `NaN` | MSL | - | 0 |
| 15 | `sensor_detection_prob` | number | `MissileTuningDefinition::sensor_detection_prob` (unit_definition.h:78) | `380 (@1450)` | `NaN` | MSL | - | 0 |
| 16 | `sensor_bearing_noise_std` | number | `MissileTuningDefinition::sensor_bearing_noise_std` (unit_definition.h:79) | `382 (@1450)` | `NaN` | MSL | - | 0 |
| 17 | `sensor_range_noise_std` | number | `MissileTuningDefinition::sensor_range_noise_std` (unit_definition.h:80) | `384 (@1450)` | `NaN` | MSL | - | 0 |
| 18 | `sensor_track_memory_s` | number | `MissileTuningDefinition::sensor_track_memory_s` (unit_definition.h:81) | `385 (@1450)` | `NaN` | MSL | - | 0 |
| 19 | `seeker_type` | int | `MissileTuningDefinition::seeker_type` (unit_definition.h:82) | `386 (@1450)` | `-1` | MSL | inferred from guidance.type | 0 |
| 20 | `seeker_activation_range_m` | number | `MissileTuningDefinition::seeker_activation_range_m` (unit_definition.h:83) | `388 (@1450)` | `NaN` | MSL | - | 0 |
| 21 | `seeker_gimbal_limit_deg` | number | `MissileTuningDefinition::seeker_gimbal_limit_deg` (unit_definition.h:84) | `390 (@1450)` | `NaN` | MSL | - | 0 |
| 22 | `seeker_ifov_deg` | number | `MissileTuningDefinition::seeker_ifov_deg` (unit_definition.h:85) | `391 (@1450)` | `NaN` | MSL | - | 0 |
| 23 | `bearing_filter_tau_s` | number | `MissileTuningDefinition::bearing_filter_tau_s` (unit_definition.h:86) | `392 (@1450)` | `NaN` | MSL | - | 0 |
| 24 | `elevation_filter_tau_s` | number | `MissileTuningDefinition::elevation_filter_tau_s` (unit_definition.h:87) | `394 (@1450)` | `NaN` | MSL | - | 0 |
| 25 | `range_filter_tau_s` | number | `MissileTuningDefinition::range_filter_tau_s` (unit_definition.h:88) | `395 (@1450)` | `NaN` | MSL | - | 0 |
| 26 | `track_break_time_s` | number | `MissileTuningDefinition::track_break_time_s` (unit_definition.h:89) | `396 (@1450)` | `NaN` | MSL | - | 0 |
| 27 | `boost_time_s` | number | `MissileTuningDefinition::boost_time_s` (unit_definition.h:90) | `397 (@1450)` | `NaN` | MSL | - | 0 |
| 28 | `sustain_time_s` | number | `MissileTuningDefinition::sustain_time_s` (unit_definition.h:91) | `398 (@1450)` | `NaN` | MSL | - | 0 |
| 29 | `boost_thrust_n` | number | `MissileTuningDefinition::boost_thrust_n` (unit_definition.h:92) | `399 (@1450)` | `NaN` | MSL | - | 0 |
| 30 | `sustain_thrust_n` | number | `MissileTuningDefinition::sustain_thrust_n` (unit_definition.h:93) | `400 (@1450)` | `NaN` | MSL | - | 0 |
| 31 | `reference_area_m2` | number | `MissileTuningDefinition::reference_area_m2` (unit_definition.h:94) | `401 (@1450)` | `NaN` | MSL | - | 0 |
| 32 | `cd0_subsonic` | number | `MissileTuningDefinition::cd0_subsonic` (unit_definition.h:95) | `402 (@1450)` | `NaN` | MSL | - | 0 |
| 33 | `cd0_supersonic` | number | `MissileTuningDefinition::cd0_supersonic` (unit_definition.h:96) | `403 (@1450)` | `NaN` | MSL | - | 0 |
| 34 | `induced_drag_k` | number | `MissileTuningDefinition::induced_drag_k` (unit_definition.h:97) | `404 (@1450)` | `NaN` | MSL | - | 0 |
| 35 | `cd0_mach_breakpoints` | array | `MissileTuningDefinition::cd0_mach_breakpoints` (unit_definition.h:98) | `405 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 36 | `cd0_mach_values` | array | `MissileTuningDefinition::cd0_mach_values` (unit_definition.h:99) | `406 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 37 | `induced_drag_k_mach_breakpoints` | array | `MissileTuningDefinition::induced_drag_k_mach_breakpoints` (unit_definition.h:100) | `407 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 38 | `induced_drag_k_mach_values` | array | `MissileTuningDefinition::induced_drag_k_mach_values` (unit_definition.h:101) | `408 (@1450)` | `[]` | MSL | parse_vector | 0 |
| 39 | `propellant_mass_kg` | number | `MissileTuningDefinition::propellant_mass_kg` (unit_definition.h:102) | `409 (@1450)` | `NaN` | MSL | - | 0 |
| 40 | `max_lateral_g` | number | `MissileTuningDefinition::max_lateral_g` (unit_definition.h:103) | `410 (@1450)` | `NaN` | MSL | seed=flight_model.max_g | 0 |
| 41 | `autopilot_tau_s` | number | `MissileTuningDefinition::autopilot_tau_s` (unit_definition.h:104) | `411 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 42 | `autopilot_damping` | number | `MissileTuningDefinition::autopilot_damping` (unit_definition.h:105) | `412 (@1450)` | `NaN` | MSL | - | 0 |
| 43 | `autopilot_order` | int | `MissileTuningDefinition::autopilot_order` (unit_definition.h:108) | `413 (@1450)` | `1` | MSL | nonzero default sentinel | 0 |
| 44 | `max_accel_response_g_per_s` | number | `MissileTuningDefinition::max_accel_response_g_per_s` (unit_definition.h:109) | `415 (@1450)` | `NaN` | MSL | used nested@guidance | 0 |
| 45 | `mach_transonic_start` | number | `MissileTuningDefinition::mach_transonic_start` (unit_definition.h:110) | `416 (@1450)` | `NaN` | MSL | - | 0 |
| 46 | `mach_transonic_end` | number | `MissileTuningDefinition::mach_transonic_end` (unit_definition.h:111) | `417 (@1450)` | `NaN` | MSL | - | 0 |
| 47 | `cd0_power_on_ratio` | number | `MissileTuningDefinition::cd0_power_on_ratio` (unit_definition.h:112) | `418 (@1450)` | `NaN` | MSL | - | 0 |
| 48 | `min_launch_range_m` | number | `MissileTuningDefinition::min_launch_range_m` (unit_definition.h:113) | `419 (@1450)` | `NaN` | MSL | alias@guidance:1475 | 0 |
| 49 | `max_launch_off_boresight_deg` | number | `MissileTuningDefinition::max_launch_off_boresight_deg` (unit_definition.h:114) | `421 (@1450)` | `NaN` | MSL | alias off_boresight_cap@guidance:1473 | 0 |
| 50 | `lobl_required` | bool | `MissileTuningDefinition::lobl_required` (unit_definition.h:115) | `422 (@1450)` | `false` | MSL | also@guidance:1479 | 0 |
| 51 | `midcourse_datalink_supported` | bool | `MissileTuningDefinition::midcourse_datalink_supported` (unit_definition.h:116) | `424 (@1450)` | `false` | MSL | also@guidance:1477 | 0 |
| 52 | `use_kalman_seeker` | bool | `MissileTuningDefinition::use_kalman_seeker` (unit_definition.h:117) | `425 (@1450)` | `false` | MSL | - | 0 |

## 2. Escape-Hatch Families (Verified Source Lines)

- **Field aliasing / dual representation.** `fuze` **and** `fuse` both route to
  `parse_fuze_json_fields` (`:1484-1489`). Engine is a nested `engine` object
  **or** flat top-level `mil_thrust_n`/`ab_thrust_n`/`sfc_mil`/`sfc_ab`/
  `bypass_ratio` (`:829-846`); the flat form overwrites the nested one when
  present. `engine_tuning` (top-level) aliases `engine.tuning` (`:847-853`);
  `aero_tuning` (top-level) aliases `airframe.tuning` (`:1000-1006`). Inside
  `fuze`/`fuse`, the trigger radius accepts `trigger_radius_m` /
  `trigger_radius` / `radius_m` (first-match `if/else-if`, `:476-482`) and
  `trigger_logic` falls back to `trigger_mode` (`:485-486`).
- **Four sensor variants (independent `if` + three-way chain).** `sensor_ref`
  (string) is an **independent** `if` (`:889-893`); `sensor_refs` (array) /
  inline `sensor` (object) / `has_sensor` (bool) form a mutually-exclusive
  `if / else-if` chain (`:894-907`) where only the first matching form wins.
  `sensor_ref` can therefore combine with any chain form — the maintained
  `ddg51_flight_i_uss_arleigh_burke.json` carries both `sensor_ref` and
  `sensor_refs`.
- **Three-source missile-tuning merge.** `parse_missile_tuning_json_fields` runs
  on the flat top-level `entry` (`:1450`), then again on nested `missile_tuning`
  (`:1453`) and on nested `guidance` (`:1457`). The `guidance` block adds
  per-key aliases: `active_seek_range` → `seeker_lock_range` (`:1469`),
  `off_boresight_cap` → `max_launch_off_boresight_deg` (`:1473`), and
  `guidance.type` → `seeker_type` inference (`:1459-1466`). `warhead`
  (`:1481-1483`) and `fuze`/`fuse` (`:1484-1489`) contribute further nested
  merges that can also set `fuse_distance`/`damage`.
- **Polymorphic / dual-form nested nodes.** A damage-component `dependencies[]`
  entry may be a bare string **or** an object (`:1232-1254`) — the only
  string-or-object polymorph in face (i). A component `failure_modes` block is
  itself dual-form: an array of mode names **or** an object of mode-to-weight
  (`:1305-1331`), with a separate `failure_mode_weights` object overlay
  (`:1332-1345`). Component geometry is a nested-vs-flat dual path: the typed
  keys are read by `parse_damage_component_geometry_json_fields` (`:84-154`,
  called at `:1351`) both as a nested `geometry` object (`primitive`, `source`,
  `vertices_m`, `thin_prism`, `obb.axes`/`half_extents_m`, `:107-145`) and as
  flat `geometry_*` keys (`:90-105`, `:146-153`), falling back to halves of the
  legacy `size`/`offset` box when no positive half-extents were given
  (`:1352-1360`).
- **Fallback chains.** A component's `offset`/`size` fall back to the parent
  hitbox (`:1277-1291`); `component.system` falls back to `component.name`
  (`:1225`).
- **Sentinels and codec presets.** `std::numeric_limits<double>::quiet_NaN()`
  "unset" markers (pervasive in `MissileTuningDefinition`), `has_*` presence
  flags, and negative int sentinels (`seeker_type = -1`,
  `data_link_max_messages_per_update = -1`) gate factory defaults;
  `autopilot_order = 1` is a deliberate nonzero content default
  (`unit_definition.h:106-108`). Five surfaces merge over named codec
  **presets**, not value-initialized zeros: `sensor` / per-mount /
  missile-seeker sensor (`make_unit_definition_default_sensor()`, 30 km —
  `:883`, `:914`, `:1491`), `sonar` / per-mount sonar
  (`make_default_sonar_definition()`, 25 km — `:886`, `:931`),
  `engine.tuning`/`engine_tuning` (`flight_dynamics::default_engine_tuning()` —
  `:838`, `:850`), `airframe.tuning`/`aero_tuning`
  (`flight_dynamics::default_aero_tuning()` — `:996`, `:1003`), and
  `landing_gear` (loader-literal paved-only preset — `:959`); `health` rests on
  the loader literal `{100,100}` (`:875`), and `flight_model` carries in-block
  fallback literals (`min_g` -3.0, takeoff 80 / landing 70 / taxi 15,
  `:951-955`).

## 3. Present-But-Unread Top-Level Keys And Census Cross-Check

Seven top-level keys appear in the 27 definition files but are **not** among the
106 keys the parser reads:

| Key | Files [U/M/W/F] | Kind |
|-----|-----------------|------|
| `_deferred_runtime_claims` | 1 [U1] | annotation (underscore-prefixed) |
| `_ground_schema` | 1 [U1] | annotation (underscore-prefixed) |
| `_provenance` | 12 [U7 M5] | annotation (underscore-prefixed) |
| `_real_world` | 3 [U3] | annotation (underscore-prefixed) |
| `ew_suite_ref` | 1 [U1] | SEMANTIC (unread by parser) |
| `rcs` | 2 [M2] | SEMANTIC (unread by parser) |
| `rcs_profile_ref` | 1 [U1] | SEMANTIC (unread by parser) |

- **Four underscore annotations** (`_provenance` ×12, `_real_world` ×3,
  `_ground_schema`, `_deferred_runtime_claims`) are provenance/schema notes,
  ignored by the parser by convention.
- **Three semantic unread keys** — `ew_suite_ref`, `rcs_profile_ref`, `rcs` —
  carry real content that the parser silently drops. Cross-check against the
  census: the census section 1(i) lists `ew_suite_ref`/`rcs_profile_ref` as
  `UnitDefinition` members (they exist: `unit_definition.h:185-186`) and says
  `spawn` "resolves `sensor_ref`/`engine_ref`/`ew_suite_ref`/`rcs_profile_ref`
  … by name". This survey refines that: `parse_unit_json` **never assigns**
  `def.ew_suite_ref` or `def.rcs_profile_ref` (grep over
  `unit_definition_loader.cpp` returns zero matches; the symbols occur only in
  `unit_definition.h` and `src/models/core/default_unit_factory.h`), so the
  spawn-time resolution operates on empty strings — a dead content edge for
  those two keys. Likewise `rcs` (the `RCSProfile` module payload) is never
  read, so the 2 `RCSProfile` module files load with only `name`+`type` and
  `UnitDefinition::rcs_data` stays default-initialized. This does **not** change
  the **106** total: those keys are present-in-data but unread, and the
  **54**/**52** split and **106** total match the census exactly. No correction
  to the census figures is required; this is an added precision about
  present-but-unread content keys, routed to the coordinator for adjudication.

## 4. Machine-Readable Schema Draft (Format And "Not Wired" Evidence)

The draft is `tools/maintenance/dto_schema/drafts/content_unit_schema_draft.json`
— a static JSON survey artifact that encodes each key's static spec: `key`,
`json_type`, `polymorphic` (top-level value-form variability only; nested
polymorphism lives in `forms_aliases` and the family text), `target` (struct /
member / decl `file:line`),
`read_site`, `default_or_sentinel`, `escape_hatch_family`, `forms_aliases`, and
`distribution`. It mirrors the T1 `dto_schema` `Field` model concepts (`name`,
`cpp_type`, `default`, `json_key`/`hidden`/`readonly` reserved binding metadata
per `tools/maintenance/dto_schema/model.py`) extended for content concerns
(aliases, polymorphic forms). It also carries `escape_hatch_families`,
`sentinel_legend`, `present_but_unread_top_level_keys`, and
`xmacro_comma_blockers`.

"Not wired" is guaranteed structurally, not by convention:

- The draft is **JSON**, not a Python module: `generate.py` only imports the
  modules listed in `tools/maintenance/dto_schema/schemas/__init__.py`
  (`SCHEMA_MODULES`); it does no directory scanning, so an unimported file
  cannot enter the generation set.
- It lives under a new `drafts/` subdirectory, **not** under `schemas/`. The
  freshness gate `tests/architecture/governance/test_dto_schema_freshness.py`
  globs `schemas/*.py` and asserts that set equals the registered manifest; a
  JSON file in `drafts/` is matched by neither the glob nor `SCHEMA_MODULES`.
- Being non-`.py`, it is outside `ruff`'s Python surface and the DTO builder.
- The file's `_draft` object states `status: "draft, not wired"` and names its
  source census. Verification in section 7 shows `generate.py --check` output
  and every generated artifact are byte-unchanged.

## 5. X-Macro Comma-Blocker Inventory

All **58** `UnitDefinition` members and all **56** `MissileTuningDefinition`
fields were scanned for type declarations carrying an angle-bracket comma (the
tokens the T1 X-macro machinery mis-splits, because the C preprocessor pairs
only parentheses). Exactly **one** member qualifies:

| Struct | Member | Type | Decl | Verdict suggestion |
|--------|--------|------|------|--------------------|
| `UnitDefinition` | `default_loadout` | `std::unordered_map<int, std::string>` | `unit_definition.h:190` | **HELD** (hand-written) per the I31 `ExecutionBatchStepResult` (`std::vector<std::array<double, 4>>`) precedent; adjudicate before any X-macro list inclusion; an alias/`typedef` exemption is explicitly ruled out (it would break the token-for-token type equivalence the migration requires). |

`MissileTuningDefinition` has **none**: its only templated members are
`std::vector<double>` (`cd0_mach_breakpoints`, `cd0_mach_values`,
`induced_drag_k_mach_breakpoints`, `induced_drag_k_mach_values`), which carry no
intra-angle comma. This confirms and completes the census red-line note that
`default_loadout` is "a known member in this class" and is the sole blocker in
the two target structs — the prerequisite adjudication for slice 4
(table-driving `unit_definition_loader`).

## 6. Red Lines (Reproduced From Census Section 3)

- **Content JSON compatibility is frozen.** `examples/config/**` (unit database
  and the 24-file experiment matrix) must not change; migration is
  bundle-by-bundle with fixture parity. The `dto_schema` generator must not join
  the normal CMake build (program non-goal).
- **ABI.** `UnitDefinition` member order (consumed field-by-field by
  `DefaultUnitFactory::spawn`) and the capability/spawn `detail/*.inc` field
  order are ABI; no reorder/retype/removal without a compatibility shell.
- **X-macro comma blockers.** Every angle-bracket-comma field (here:
  `default_loadout`) must be explicitly adjudicated (held, or an alias exemption
  explicitly ruled) before it enters an X-macro list, per the I31 precedent.
- **Codec escape hatches must be preserved.** The `fuze`/`fuse` alias, engine
  flat-vs-nested, `engine_tuning`/`aero_tuning` dual paths, the
  `sensor_ref`/`sensor_refs`/inline/`has_sensor` variants, the
  entry+`missile_tuning`+`guidance` triple-source merge, and the
  string-or-object `dependencies[]` polymorphism are external JSON contract, not
  accidents.
- **Sentinel semantics.** NaN "unset" markers and `has_*` presence flags gate
  factory defaults; their meaning must survive any codec migration.
- **Materialization behaviour.** `spawn()` entity output must stay
  byte/behaviour-identical (pinned by `test_naval_ship_database.py`, the
  `platform_spawn` suite, and the weapon-guidance realism suites).
- **Additive extension.** New validation / stages arrive behind versioned or
  opt-in paths with regeneration freshness gates; compatibility shells retire
  only at the T7 final residual audit.

## 7. Verification

- `python tools/maintenance/dto_schema/generate.py --check` — all outputs
  up-to-date; `git diff` over the generated tree
  (`gym_envs/scenario_loader/_generated/` and `src/**/detail/*.inc`) is empty,
  proving the draft is not wired.
- `python tools/maintenance/document_link_audit.py` — 0 issues.
- `python tools/maintenance/translate_docs_batch.py audit` — the new pair
  `plan/unified_architecture_program/t11_content_schema_survey_20260721` reports
  as `unregistered` (its `pair_id` is not yet in
  `docs/engineering/documentation/reference/bilingual_document_clusters.json`); `pair_count` rises 84 → 85
  while `synced` stays 84 and `diverged`/`missing` stay 0. The registry refresh
  (`clusters --write`) and iteration-ledger registration are the landing party's
  step, per the census section 5 scoping precedent.
- `git diff --check` — clean (only new untracked files added; no tracked-file
  whitespace changes). `ruff` is not applicable to the draft (it is JSON).
- Bilingual self-check — English and Chinese carry the same heading count, the
  same table row counts (54 / 52 / 7 body rows), and equal occurrence counts of
  the key figures (106, 54, 52, 58, 56, 27).

## Related Authority

- [T11 Content Compilation Pipeline Census (2026-07-21)](t11_content_pipeline_census_20260721.md) (the census this slice extends; section 3 slice order and red lines)
- [Unified Architecture Program](README.md) (T11 track definition and risk; T3 loader item)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md) (SCAL Semantic Graph face; `P0 ContentCompile`)
- [Repository Consolidation Plan](../repository_consolidation/README.md) (iteration ledger and protocol)
