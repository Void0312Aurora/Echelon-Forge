#pragma once

// T11 slice 3 (I55): declared ContentCompile passes behind the unit loader API.
//
// The maintained entry point `load_unit_definitions_json` is a thin orchestrator
// that runs the unit compile in the P0 ContentCompile stage order:
//
//     parse_pass  ->  validate_pass  ->  resolve_pass  ->  (materialize @ spawn)
//
// Only `parse` and (spawn-side) `materialize` are behaviour-bearing today. This
// slice introduces a real `validate` pass (structural schema diagnostics) and an
// explicit `resolve` pass boundary WITHOUT changing any load or spawn behaviour:
// `validate_pass` never throws, rejects, or mutates and its output is discarded
// on the maintained path; `resolve_pass` is a read-only pass-through that does
// not move reference resolution earlier than the factory materialize step.
//
// Vocabulary and scope follow:
//   - docs/plan/archive/unified_architecture_program_completed_20260727/
//     t11_content_pipeline_census_20260721.md
//     (section 3 slice order, step 3; red lines)
//   - docs/plan/archive/unified_architecture_program_completed_20260727/
//     t11_content_schema_survey_20260721.md
//     (the 106 recognized top-level keys + 7 present-but-unread keys)

#include <cstddef>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "content/unit_definition.h"

namespace content_compile {

// A single non-fatal diagnostic produced by the validate pass. The validate
// pass never throws, never rejects, and never mutates data; it only produces
// these records, which the maintained load path discards.
struct ContentDiagnostic {
    enum class Severity { Info, Warning };

    Severity severity = Severity::Warning;
    std::string source;    // originating file path / logical origin (best-effort)
    std::string unit_name; // best-effort unit name; empty when unknown
    std::string code;      // stable machine code, e.g. "unknown_top_level_key"
    std::string key;       // offending key when applicable
    std::string message;   // human-readable description
};

// -------------------------------------------------------------------------
// Parse pass
// -------------------------------------------------------------------------
// Defined in unit_definition_loader.cpp because it drives the hand-written
// mapping helpers (parse_unit_json / parse_missile_tuning_json_fields / ...)
// that are translation-unit-local to that file.
//
// Byte/behaviour-identical to the historical directory/single-file load walk:
// same traversal order, same vulnerability-evidence descriptor pre-load, same
// first-failure error strings, the same outer guard that catches only
// std::filesystem::filesystem_error, and the same std::stoi / get<std::string>
// throw paths left uncaught (the unified error surface is a later slice).
//
// When `out_raw_entries` is non-null it also receives each parsed unit's raw
// top-level JSON object, purely so the validate pass can inspect it; capturing
// changes no parsed UnitDefinition output.
bool parse_pass(const std::string &path, std::vector<UnitDefinition> &out_definitions,
                std::string *error, std::vector<nlohmann::json> *out_raw_entries = nullptr);

// -------------------------------------------------------------------------
// Validate pass
// -------------------------------------------------------------------------
// True when `key` is a recognized top-level content key: the union of the 106
// parser-read keys (54 direct + 52 missile-tuning), the three semantic
// present-but-unread keys (ew_suite_ref / rcs / rcs_profile_ref), and the
// underscore-annotation convention (any key beginning with '_'). Hardcoded from
// the I52 survey; the draft JSON is NOT read at build or run time.
bool is_recognized_top_level_key(const std::string &key);

// Validate a single top-level unit JSON object. Returns structural diagnostics
// (currently one "unknown_top_level_key" warning per unrecognized top-level
// key). Never throws, never mutates, never rejects; a non-object input yields no
// diagnostics.
std::vector<ContentDiagnostic> validate_unit_json_entry(const nlohmann::json &entry,
                                                        const std::string &source = "");

// Validate pass: batch form over the raw top-level entries captured by the parse
// pass. Aggregates per-entry diagnostics; never throws, mutates, or rejects.
std::vector<ContentDiagnostic> validate_pass(const std::vector<nlohmann::json> &entries,
                                             const std::string &source = "");

// -------------------------------------------------------------------------
// Resolve pass
// -------------------------------------------------------------------------
// A read-only summary of the cross-references that stay deferred to the
// materialize step. DefaultUnitFactory::spawn /
// build_platform_capability_bundle_template
// (src/models/core/default_unit_factory.h) resolve these names via
// definitions_.find(...) at spawn time; this slice does not change that timing.
struct DeferredReferenceReport {
    std::size_t definitions = 0;
    std::size_t sensor_ref = 0;
    std::size_t sensor_refs = 0;
    std::size_t engine_ref = 0;
    std::size_t ew_suite_ref = 0;    // present-but-unread: parser never populates it
    std::size_t rcs_profile_ref = 0; // present-but-unread: parser never populates it
    std::size_t default_loadout = 0;
    std::size_t embarked_helo_ref = 0;
    std::size_t definitions_with_deferred_refs = 0;
};

// Resolve pass: an explicit PASS-THROUGH. Reference resolution stays deferred to
// the factory/spawn materialize step (unchanged timing); this pass only tallies
// the deferred edges for observability and MUST NOT mutate `definitions`.
DeferredReferenceReport resolve_pass(const std::vector<UnitDefinition> &definitions);

} // namespace content_compile
