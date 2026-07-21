# T11 Content Compilation Pipeline Census (2026-07-21)

Language:
- English canonical: `t11_content_pipeline_census_20260721.md`
- Chinese companion: [t11_content_pipeline_census_20260721.zh.md](t11_content_pipeline_census_20260721.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t11_content_pipeline_census_20260721.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `9a054c0a`

Status: T11 first-slice content-surface census for the
[Unified Architecture Program](README.md). T11's charter is to "evolve
scenario/unit content loading into the staged `P0 ContentCompile` model: typed
setup packets, capability-bundle expansion behind `spawn_unit` compatibility,
content schema validation as a compile stage; absorbs and supersedes the T3
loader item", with the target that "new content and new domains enter through
compiled, validated capability composition" and the key risk that "content JSON
compatibility is a hard external surface; migration must be bundle-by-bundle
with fixture parity". This document is a descriptive census register
(`reference`), not an independent review: it records the verified baseline state
and carries no review verdict. It changes no behavior and no `src/**` /
`python/**` code; it inventories what exists so later T11 slices can extend it
under the red lines in section 3. Vocabulary follows the SCAL Semantic Graph
face and the `P0 ContentCompile` stage in
[Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
(section 6 lifecycle table row `P0 ContentCompile`; section 6.1 stage-contract
amendment).

## 0. Method And Scope

- Surveyed the maintained content surface at baseline `9a054c0a`:
  `src/content/**` and `src/models/core/default_unit_factory.h` (read-only),
  `src/runtime/contracts/platform_capability_contracts.h`,
  `python/scenario/**`, `python/experiment/**`,
  `gym_envs/scenario_loader/**`, `tools/maintenance/dto_schema/schemas/**`,
  `tools/maintenance/experiment_matrix/**`, `examples/config/**` (read-only),
  and the pinning tests under `tests/**` and `src/tests/**`.
- The `P0 ContentCompile` reference definition used throughout is the section-6
  lifecycle row: owner `content/` + adapters + facade setup; inputs "scenario
  files, unit data, backend capability requests"; outputs "typed setup packets,
  content ids"; must-not-own "per-tick behavior". The analytic decomposition
  **parse -> validate -> resolve -> materialize** used in the gap matrix
  (section 2) is this census's lens, not doc-verbatim: the architecture defines
  P0 by its inputs/outputs/must-not-own and by the section-6.1 stage-contract
  fields (`semantic_stage`, `sub_graph`, `read_set`/`write_set`,
  `clock_domain`, `information_layer_*`, `extension_points`), and does not name
  those four sub-stages. Places where the doc is silent are marked
  **(undecided)**.
- Quantitative loader figures were counted directly over
  `src/content/unit_definition_loader.cpp` at `9a054c0a` (regex match counts;
  reproduced in section 1(i)).
- Zero behavior change. No optional read-only architecture test was added; the
  decision and its rationale are recorded in section 4.

## 1. Content-Surface Census

### (i) Unit definition loader (JSON -> `UnitDefinition`)

| Aspect | Finding |
|--------|---------|
| Entry point | `load_unit_definitions_json(path, out_definitions, error)` (declared `src/content/unit_definition_loader.h:37`; defined `unit_definition_loader.cpp:1836-1881`). A directory path first loads the vulnerability-evidence descriptors (via `load_vulnerability_evidence_descriptors`, `:1634`), then runs `fs::recursive_directory_iterator` over every `.json` whose **direct** parent is not `damage/vulnerability_evidence/`: the skip test `entry.path().parent_path() == vulnerability_evidence_dir` (`:1855`) compares only the immediate parent, so it excludes the two descriptor files themselves but would **not** exclude a hypothetical nested subtree beneath that folder (no such nesting exists today, so behaviour is currently equivalent to a subtree skip). A file path goes straight to `load_file` (`:1587-1632`), which accepts either a `{"units": [...]}` array or a single object carrying `name`+`type`, else errors `"expected 'units' array or a single unit object"`. The C++ pins load the whole `examples/config/database` tree via `SimulationKernel::load_database`/`load_definitions` (`src/core/engine/simulation_kernel.cpp:173,213`), so the recursive walk feeds **all 27 definition files** through `load_file` -> `parse_unit_json` (not just the units): **11 unit-platform files** (`aircraft/units/*.json` x5, `ships/units/*.json` x5, `ground/units/*.json` x1); **12 module files** (`aircraft/modules/{engines x2, ew_suites x1, rcs_profiles x2, sensors x2}` + `ships/modules/sensors x5`, parsed as `Engine`/`EWSuite`/`RCSProfile`/`Sensor` definitions); **3 weapon files** (`weapons/air_to_air/*.json`, `type: Missile`); and **1 facility file** (`facilities/generic_airbase.json`, `type: Facility`). Every one carries top-level `name`+`type` and lands in the same `name -> UnitDefinition` map, so units resolve `engine_ref`/`sensor_ref`/`ew_suite_ref`/`rcs_profile_ref`/`default_loadout` by name (e.g. `f16c_block50.json` -> `"F110-GE-129"`, `"AN/APG-68(V)9"`, `"AIM-120C-7"`). The 2 `damage/vulnerability_evidence/*.json` descriptors load through the separate descriptor path, for 29 JSON files total under the database root. |
| Intermediate representation | The single hand-written mapper `parse_unit_json` (`:804-1585`, ~782 lines) fills a flat `UnitDefinition` struct (`src/content/unit_definition.h:177-265`) of 58 direct members (counted field-by-field): type/name, component **refs** (`sensor_ref`, `sensor_refs`, `engine_ref`, `ew_suite_ref`, `rcs_profile_ref`), `hardpoints`, `default_loadout` (`unordered_map<int,string>`), inline component blocks (`engine_data`, `jammer/rwr/esm/cms`, `rcs_data`, `airframe`, ship/submarine platforms, naval stores/logistics/weapon system, embarked air ops, `damage_model` `HitboxConfig`, `aircraft_vulnerability`, `health`, `sensor`+`mounted_sensors`, `sonar`+`mounted_sonars`, `flight_model`, `stall_state`, `landing_gear`, `score`, `ammo`, `command_link`, data-link scalars, and a 56-field `MissileTuningDefinition` at `unit_definition.h:63-122`). |
| Escape-hatch / hand-mapping quantification (verified at `9a054c0a`) | `unit_definition_loader.cpp` = **1,881 lines** (100 blank; the `Measure-Object -Line` reading of 1,781 excludes blanks) — matches the README T3 "1,881-line hand mapping". Call-site counts: `.value(key, default)` **x430**; `.contains(key)` **x79**; type guards `.is_object()` **x50**, `.is_array()` **x23**, `.is_number()` **x12**, `.is_string()` **x7**, `.is_boolean()` **x0**; explicit `.get<...>()` **x25**. `parse_unit_json` accesses **54 distinct top-level JSON keys directly**, and for a missile-type unit additionally routes the *entire* `entry` through `parse_missile_tuning_json_fields` (`:1450`), which reads **52 further distinct top-level keys** disjoint from the 54 (the maintained `aim_120c.json` genuinely carries top-level `max_flight_time_s`), for a **semantic total of 106 recognized top-level keys**. Sixteen hand-written `parse_*` helpers (e.g. `parse_vec3_array`, `parse_sensor_json_fields`, `parse_missile_tuning_json_fields`, `parse_unit_type`, `parse_sensor_type_code`). Escape-hatch patterns: **field aliasing / dual representation** — `fuze`+`fuse` both parsed (`:1484-1489`); engine as nested `engine` object **or** flat `mil_thrust_n`/`ab_thrust_n`/`sfc_mil`/`sfc_ab`/`bypass_ratio` (`:830-846`); `engine_tuning` top-level vs `engine.tuning`; `aero_tuning` vs `airframe.tuning`; sensor via `sensor_ref` / `sensor_refs` / inline `sensor` / `has_sensor` (`:889-906`); missile tuning merged from flat `entry` **and** `missile_tuning` **and** `guidance` with per-key aliases (`active_seek_range`, `off_boresight_cap`) (`:1450-1480`). **Polymorphic node** — a damage-component `dependencies[]` entry may be a bare string **or** an object (`:1232-1254`). **Fallback chains** — component `offset`/`size` fall back to the parent hitbox (`:1277-1291`); `component.system` falls back to `component.name` (`:1225`). **Sentinels** — `std::numeric_limits<double>::quiet_NaN()` "unset" markers plus `has_*` presence flags plus `-1` int sentinels. **Not schema-sourced**: there is no `unit_definition_*`/`content_*` file under `tools/maintenance/dto_schema/schemas/` (contrast: `capability_bundle_fields.py`, `platform_capability_fields.py`, `typed_platform_spawn_*_fields.py`, `world_spawn_request_fields.py` are schema-sourced). |
| Consumers (resolve + materialize) | `DefaultUnitFactory` (`src/models/core/default_unit_factory.h`) owns a `name -> UnitDefinition` map. `spawn(ecs, unit_name, params)` (`:619-1439`, 821 physical lines incl. the closing brace) **gates then materializes**: it calls `resolve_platform_spawn_plan_for_type_name` -> `build_platform_capability_bundle_template` (`:321-531`, derives a `CapabilityBundle` from the struct's `has_*` flags into sensing/mobility/communication/command/launching/survivability/doctrine capabilities with synthesized `evidence_refs`) -> `validate_resolved_platform_spawn_plan`, rejecting to `flecs::entity::null()` on failure; then hand-materializes the flecs entity, resolving `sensor_ref`/`engine_ref`/`ew_suite_ref`/`rcs_profile_ref`/`default_loadout`/`embarked_air_ops.helo_unit_name` by `definitions_.find(...)` at spawn time. The typed contract layer is `runtime::platform_capabilities` (`src/runtime/contracts/platform_capability_contracts.h`): schema-sourced `Capability`/`CapabilityBundle`/`ResolvedPlatformSpawnPlan` structs (`detail/*.inc`) with fail-closed validators; request kinds `type_name_projection` / `typed_platform_request`; materialization strategies `factory_projection_materialization` / `resolved_spawn_plan_bridge`. Only the `type_name_projection` + `factory_projection_materialization` path has a producer today. |
| Test pinning | C++ `src/tests/test_components_basic.cpp`; Python `tests/architecture/platform_spawn/` (6 files: `test_platform_capability_contracts.py`, `test_typed_platform_spawn_contracts.py`, `test_default_factory_spawn_plan_resolution.py`, `test_default_factory_spawn_command_projection.py`, `test_boundary_guards.py`, `test_runtime_setup_consume_bridge.py` — **none smoke-gated**); `tests/runtime/naval/test_naval_ship_database.py` (**smoke**); weapon-guidance realism suites under `tests/runtime/air_combat/weapon_guidance_realism/` consume unit defs. |
| Gap vs `P0 ContentCompile` | **parse** is a 1,881-line hand mapping, not schema-sourced (the T3/T11 target). **validate** at parse is structural-only (type present+known, units/single object) plus the I47 vulnerability-authority downgrade (`:1397-1409`) and the descriptor `dataset_id`+`target_type` requirement (`:1810`); the only fail-closed structured validation (`validate_capability_bundle`) runs at **spawn** (materialize), not as a compile stage. **resolve** (cross-refs) and **materialize** are interleaved inside `spawn()`. The `CapabilityBundle` is a **projection derived from** the monolithic struct, not the source of truth, and the `typed_platform_request` path (real `spawn_platform({capabilities...})`) has no content-fed producer. Output is a flecs entity, not the doc's "typed setup packets + content ids". |

### (ii) Scenario JSON loading and compile chain

| Aspect | Finding |
|--------|---------|
| Entry point | `ScenarioCompiler.compile_path(source_path)` / `compile_data(scenario_data)` (`python/scenario/compiler/service.py:82-99`), with a class-level `_path_cache` and a freshness gate (`CompiledScenario.is_fresh` over `dependency_mtimes_ns`, `:63-71`; cache hit re-validated at `:84-90`). The canonical-owner boundary is enforced by a smoke test (see pinning). |
| Intermediate representation / stages | `_compile_from_data` (`:110-185`) runs an ordered pipeline: (1) **parse** `_compile_from_path` `json.load`, must be a dict (`:102-107`); (2) **validate (shape)** `validate_scenario_compiler_shape` (`compiler/validation.py:74-149`) — optional-dict/list shapes, `_require_object_entries`, `_require_unique_entity_names`; docstring states it validates "only the shapes the compiler consumes directly"; (3) **resolve/merge** `_compile_merged_scenario_data` (prefab merge + `imports` resolution -> `merged, imported_files, warnings`); (4) **ingest** `ingest_projection_setup_payloads_into_scenario` (environment substrate; fail-closed with `rejection_reason`, `:119-126`); (5) **re-validate** the merged doc (`:128-132`); (6) **materialize** a typed IR `CompiledScenarioRuntimeMetadata` (mission-command template, rewards, waypoint cache, layout template, conditional objectives, ILS beacons) into the frozen `CompiledScenario` dataclass (`:43-71`, `:175-185`). |
| Consumers (materialize to kernel) | `gym_envs/scenario_loader/core.py::ScenarioLoader` holds `_compiled_scenario`/`_compiled_runtime_metadata` and exposes `load_scenario`/`load_compiled_scenario`/`load_scenario_data` (`:355-361`); it delegates to owner modules via `__getattr__`/`__setattr__` (`:180-216`). The runtime materialization is `python/scenario/runtime/kernel_apply.py::apply_world_layout_to_kernel` (`:339`), which per spawn calls `sim.spawn_unit(side, type_name, x, y, z, heading, pitch, roll, vx, vy, vz)` (`:389`) — i.e. it re-enters face (i) through the `type_name` string. |
| Test pinning | `tests/scenario/test_scenario_compiler.py` (**smoke**); `tests/scenario/test_scenario_generation_contracts.py` (**smoke**); `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py::test_maintained_python_paths_use_the_canonical_scenario_compiler_owner` (**smoke**); `tests/scenario/test_environment_projection_contracts.py`; `tests/world_batch/test_batch_scenario_runtime.py`. |
| Gap vs `P0 ContentCompile` | This is the closest existing analogue to P0: it already stages parse -> validate -> merge/resolve -> ingest -> materialize with a freshness cache and a typed IR. Gaps: (a) it lives in the Python Experiment World (`python/scenario/compiler`), while the doc names P0's owner as `content/` + adapters + facade setup; (b) validation is shape-only with no schema and **no cross-content check** — e.g. an entity `type_name` is never verified against the unit database at compile time, only at spawn (warn/reject); (c) it is **unlinked** from the unit compile (face i) — the two pipelines meet only at the `spawn_unit(type_name)` string; (d) the IR is dict-shaped `merged_scenario_data` + ad-hoc dataclasses, not the doc's "typed setup packets" DTOs. |

### (iii) Experiment matrix -> run configuration expansion (I30)

| Aspect | Finding |
|--------|---------|
| Entry point / owner | `python/experiment/` is the T5 Experiment-face owner. `definition.py` freezes `Experiment = ScenarioRef x ConfigComposition x SeedSpec x EvaluationProtocol` as validated frozen dataclasses and an `ExperimentRegistry` registration socket (fail-fast on duplicate/dangling refs, `:153-225`). `composition.py` owns deterministic `compose_config(base, delta)` (base key order preserved, delta keys appended), `freeze_json_mapping`, `ensure_json_value`. `air_combat_matrix.py` (868 lines) is the registered air-combat matrix (I30). `report_envelope.py` is the I44 opt-in report envelope. |
| Intermediate representation / output | Run configs are **projections** of the registered definitions; rendering to files is owned by the generator `tools/maintenance/experiment_matrix/generate.py` (freshness-gated). The on-disk output is the **24-file** air-combat matrix `examples/config/training/active/air_combat/*.json` (count verified = 24). The package is standard-library only (imports no runtime/gym/training deps by design). |
| Consumers | Training/evaluation entrypoints load the rendered run-config JSON, which supplies the scenario reference that enters the scenario compiler (face ii). |
| Test pinning | `tests/experiment/test_experiment_definition.py`; `tests/experiment/test_report_envelope.py`; `tests/architecture/governance/test_experiment_matrix_freshness.py` (**smoke** — regeneration freshness gate over the matrix). |
| Gap vs `P0 ContentCompile` | This face is the **Experiment face** (T5 / baseline amendment (a)), which sits **upstream of** P0: it chooses *which* scenario/config to compile; it is not content compilation itself. It is already the most mature staged/declarative/registration-based system of the four faces (typed definition + deterministic composition + generator + freshness gate). Its P0-relevant gap is a **boundary** one: it should stay owned by T5 and **not** be folded into T11; T11 consumes the scenario ref it produces. Registered-but-held: the §1.5 curriculum-stage / comparability constraints are named but deliberately not yet fields (`definition.py` docstring). Inclusion here is census context, not a T11 work item. |

### (iv) Content validation, defaults, and versioning

| Aspect | Finding |
|--------|---------|
| Validation surfaces | **Unit**: structural-only at parse; vulnerability-evidence descriptors require `dataset_id`+`target_type` (`unit_definition_loader.cpp:1810`); authority flags downgraded unless calibrated evidence matches (I47, `:1397-1409`); no JSON schema. **Scenario**: `validate_scenario_compiler_shape` (shape-only, run twice) + fail-closed environment ingestion. **Experiment**: strong construction-time validation (identifier regex, seed normalization, JSON-safe deep-freeze, registry dangling-ref checks). **Capability/spawn**: fail-closed `validate_capability`/`validate_capability_bundle`/`validate_resolved_platform_spawn_plan` with a rejection-reason vocabulary — but invoked at spawn, not at content-compile. |
| Defaults | **Unit**: pervasive inline `.value(key, default)`, NaN sentinels, `make_unit_definition_default_sensor()` / `default_aero_tuning` / `default_engine_tuning`, six built-in `DefaultUnitFactory` definitions (Aircraft/Missile/Ship/Submarine/Facility/AWACS), and procedural `generate_default_hitboxes`; missing keys silently default. **Scenario**: `.get(key, default)` plus reward-metadata builders. **Experiment**: explicit typed dataclass defaults. |
| Versioning | **Unit JSON has no top-level version field** (verified: `examples/config/database/aircraft/units/f16c_block50.json` carries none). Versioning exists only in nested evidence blocks — `kVulnerabilityEvidenceSchemaVersion = "a2.vulnerability_evidence.v1"`, `kVulnerabilitySurrogateValidationManifestSchemaVersion = "a2.vulnerability_surrogate_validation.v1"` (`:17-19`) — and on the Python side as `SCENARIO_GENERATION_REQUEST_CONTRACT_VERSION` (scenario generation), `ENVELOPE_SCHEMA_VERSION` (report envelope, I44), and the "WP14-A vocabulary" constants (capability/spawn). Content versioning is therefore fragmented: no unified content schema version. |
| Error-report shape | **Unit**: `std::string* error` out-parameter + `bool` return, first-failure-returns (no accumulation), plus `spdlog::warn/error` for unknown refs at materialize. Not every failure is routed through that out-parameter: several unit-mapping paths call unchecked converters that **throw** — `std::stoi(key)` and `val.get<std::string>()` on `default_loadout` entries (`:871`), plus unchecked `entry["engine_ref"].get<std::string>()` (`:826`) / `entry["sensor_ref"].get<std::string>()` (`:890`) / `t.get<std::string>()` for hardpoint `type` elements (`:862`). `load_unit_definitions_json` wraps the walk in a `try` that catches only `fs::filesystem_error` (`:1871`), so a non-integer `default_loadout` key (`std::invalid_argument`) or a non-string ref (`nlohmann::json::type_error`) escapes the loader **uncaught** rather than becoming a `bool`/`error` failure. **Scenario**: `_compile_from_path` raises `ValueError` with source-path context on non-dict file content (`service.py:105`), but the `compile_data` entry raises `TypeError` on a non-dict argument (`:94`) and `_compile_from_data` raises `ValueError` on failed environment ingestion (`:122`) — so the scenario face surfaces both `TypeError` and `ValueError`, not `ValueError` alone. **Experiment**: raises `ValueError`/`TypeError`/`KeyError` at construction/registration. **Capability**: structured `PlatformCapabilityValidationResult{valid, fail_closed, rejection_reason, errors[]}`. |
| Gap vs `P0 ContentCompile` | No unified content-validation compile stage and no content schema version; unit-parse validation is minimal and scenario-parse validation is shape-only; the four faces report errors in four different shapes; the only structured fail-closed validation runs at spawn, not compile. |

## 2. Gap Matrix Against The Staged P0 Model

Rows are the analytic sub-stages (section 0 lens); cells state where each face
stands today. "SoT" = source of truth.

| Sub-stage | (i) Unit | (ii) Scenario | (iii) Experiment |
|-----------|----------|---------------|------------------|
| parse | 1,881-line hand mapping, not schema-sourced | `json.load` + shape guard | declarative dataclass construction |
| validate | structural-only at parse; capability validation deferred to spawn | shape-only, x2, no schema, no cross-content ref check | strong at construction (regex/normalize/freeze/registry) |
| resolve | refs resolved lazily inside `spawn()` (interleaved with materialize) | prefab merge + imports at compile; `type_name` resolved at spawn | base+delta `compose_config` |
| materialize | 821-line hand `spawn()` -> flecs entity (no typed setup packet) | typed IR `CompiledScenario` -> `apply_world_layout_to_kernel` -> `spawn_unit` | generator renders run-config JSON (freshness-gated) |
| stage-contract (§6.1) fields declared | none | none (implicit stage order only) | n/a (upstream Experiment face) |

Cross-cutting gaps:

- **G-A Two unlinked content pipelines.** Unit compile (C++, face i) and
  scenario compile (Python, face ii) share no typed contract; they meet only
  via the untyped `spawn_unit(type_name)` string. P0 wants one staged compile
  emitting typed setup packets + content ids.
- **G-B Parse is hand-written, output contract is generated.** The *input*
  parse (`UnitDefinition` + 1,881-line mapper) is hand-maintained while the
  *output* contracts (`CapabilityBundle`, typed platform spawn) are already
  schema-sourced under `dto_schema`. T11/T3 closes exactly this asymmetry.
- **G-C Capability bundle is a projection, not a SoT.** `spawn_unit ->
  CapabilityBundle` expansion exists (the architecture's convenience-shortcut
  target), but the bundle is derived from the monolithic struct; the
  `typed_platform_request` / `spawn_platform({capabilities...})` direction where
  "a new domain contributes capability implementations" has no content-fed
  producer.
- **G-D No content-compile validation stage / content schema version.**
  Validation is structural at unit parse and shape-only at scenario parse;
  there is no content schema version and four divergent error-report shapes.
- **G-E Owner mismatch.** The most P0-like staging lives in the Python
  Experiment World (`python/scenario/compiler`), not in the doc's P0 owner
  (`content/` + adapters + facade). **(undecided)** whether P0 ownership should
  migrate the scenario compile toward `content/`/facade or be satisfied by a
  declared facade-setup boundary — routed to the architecture workline.

## 3. Suggested Later-Slice Order And Red Lines

Suggested T11 slice order after this census. Per the program sequencing, T11
"follows the T1 escape-hatch validation and supersedes the T3 loader item";
each slice is bundle-by-bundle with fixture parity.

1. **Freeze census + gaps + red lines (this slice).**
2. **Content escape-hatch schema survey (docs + schema draft; no parse change).**
   Formalize the 106 semantic top-level keys (54 accessed directly + 52 via the
   missile-tuning helper) and the alias / polymorphic / sentinel patterns of
   face (i) — across all 27 definition files (unit platforms, modules, weapons,
   facility), not just the 11 unit-platform files — as a content-schema
   specification, reusing the T1 `dto_schema` codec escape-hatch precedent
   (inheritance registration, JSON aliases, hidden slices). Deliverable is a
   schema draft + survey, not a code swap.
3. **Stage the unit compile behind the current API.** Split parse -> validate
   -> resolve -> materialize as *declared* passes behind
   `load_unit_definitions_json`/`spawn`, introducing a real validate pass
   (schema) and a resolve pass (reference resolution) while keeping `spawn()`
   materialization byte/behaviour-identical.
4. **Table-driven `unit_definition_loader` (the T3 loader item).** Move the
   1,881-line hand mapping onto the T1 machinery, bundle-by-bundle with
   embedded-reference fixture parity — but known angle-bracket-comma member
   types (e.g. `default_loadout`'s `std::unordered_map<int, std::string>`) are a
   known obstacle that must be adjudicated first per the I31 precedent before an
   X-macro list can absorb them (see red lines).
5. **Capability bundle as source of truth.** Let content define capability
   bundles directly (the `typed_platform_request` path) so
   `spawn_platform({capabilities...})` works without deriving from the
   monolithic struct; new domains attach by capability registration (G5).
6. **Unify content validation + error reporting + content schema version**
   across unit and scenario faces.
7. **(Boundary)** Keep the T5 Experiment face and the scenario-compiler owner
   distinct; link unit+scenario compile through typed setup packets rather than
   merging the pipelines. Route the P0-ownership question (G-E) to the
   architecture workline.

**Red lines** (T11 key risk: content JSON is a hard external surface):

- **Content JSON compatibility is frozen.** `examples/config/**` (unit
  database and the 24-file experiment matrix) must not change; migration is
  bundle-by-bundle with fixture parity. The `dto_schema` generator must not
  join the normal CMake build (program non-goal).
- **ABI.** `UnitDefinition` member order (consumed field-by-field by
  `DefaultUnitFactory::spawn`) and the capability/spawn `detail/*.inc` field
  order are ABI; no reorder/retype/removal without a compatibility shell.
- **X-macro comma blockers (table-driving, step 4).** The T1 X-macro machinery
  mis-splits any member whose type declaration carries an angle-bracket comma,
  because the C preprocessor pairs only parentheses; a type-alias workaround
  would break the token-for-token type equivalence the migration requires. The
  iteration ledger's I31 entry already held the same-shape
  `ExecutionBatchStepResult` (its `std::vector<std::array<double, 4>>` field)
  fully hand-written for exactly this reason. `UnitDefinition::default_loadout`
  (`std::unordered_map<int, std::string>`, `unit_definition.h:190`) is a known
  member in this class; every such angle-bracket-comma field must be explicitly
  adjudicated (held, or an alias exemption explicitly ruled) before it enters an
  X-macro list.
- **Codec escape hatches must be preserved.** The `fuze`/`fuse` alias, engine
  flat-vs-nested, `engine_tuning`/`aero_tuning` dual paths, the
  `sensor_ref`/`sensor_refs`/inline/`has_sensor` variants, the
  entry+`missile_tuning`+`guidance` triple-source merge, and the string-or-object
  `dependencies[]` polymorphism are external JSON contract, not accidents.
- **Sentinel semantics.** NaN "unset" markers and `has_*` presence flags gate
  factory defaults; their meaning must survive any codec migration.
- **Materialization behaviour.** `spawn()` entity output must stay
  byte/behaviour-identical (pinned by `test_naval_ship_database.py`, the
  `platform_spawn` suite, and the weapon-guidance realism suites).
- **Additive extension.** New validation / stages arrive behind versioned or
  opt-in paths with regeneration freshness gates; compatibility shells retire
  only at the T7 final residual audit.

## 4. Read-Only Architecture-Test Decision

The slice budget permits at most one optional read-only architecture test to
pin an otherwise-unguarded content surface. None was added, for two reasons:

1. **Already pinned.** Each face has existing pins (section 1), several
   smoke-gated: `test_naval_ship_database.py` (unit database),
   `test_scenario_compiler.py` / `test_scenario_generation_contracts.py` /
   `test_scenario_setup_facade_boundary.py` (scenario compile),
   `test_experiment_matrix_freshness.py` (experiment matrix), plus the
   non-smoke `platform_spawn` suite for the capability/spawn contracts.
2. **Avoid cementing the state T11 must replace.** The most obviously
   "unguarded" facts are the hand-mapping escape hatches and the
   projection-only capability bundle that T11 is chartered to convert; pinning
   them now would obstruct the migration rather than protect it.

This keeps the slice pure census + documentation, consistent with the
zero-behavior-change discipline and the T10 / SCAL census precedent.

## 5. Verification

- Baseline (before this doc) maintained smoke at `9a054c0a`:
  **459 passed, 45 subtests passed** in 148.84s
  (`tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json`,
  `CMO_BUILD_DIR=build-local-win`). The `ef_core`/`ef_py` build re-configured
  cleanly for the I46 `ef_content` split ("ninja: no work to do").
- Adding this bilingual doc pair without a `clusters --write` registry refresh
  (deliberately deferred per the slice discipline) makes the smoke-gated
  `tests/architecture/governance/test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`
  mark the new unregistered pair. The registry refresh and iteration-ledger
  registration are the landing party's step (the T10 and SCAL census precedents
  made the same scoping call). The exact before/after smoke numbers are recorded
  in the iteration ledger entry.

## Related Authority

- [Unified Architecture Program](README.md) (T11 track definition and risk; T3 loader item)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md) (SCAL Semantic Graph face; `P0 ContentCompile`; section 6.1 stage contracts)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md) (T0 census precedent and format)
- [T10 Evidence Spine Census (2026-07-21)](t10_evidence_spine_census_20260721.md) (adjacent census precedent)
- [T6 Residual Ledger (2026-07-20)](t6_residual_ledger.md)
- [Repository Consolidation Plan](../repository_consolidation/README.md) (iteration ledger and protocol)
