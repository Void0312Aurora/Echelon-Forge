from __future__ import annotations

import textwrap

from tests.architecture.helpers import (
    REPO_ROOT,
    compile_cpp_snippet,
    dependency_include_path,
)

DEFAULT_UNIT_FACTORY_HEADER = REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
PLATFORM_SPAWN_INCLUDE_PATHS = (
    dependency_include_path("spdlog"),
    dependency_include_path("flecs"),
    dependency_include_path("nlohmann_json"),
)


def _compile_and_run(source: str):
    return compile_cpp_snippet(
        source,
        include_paths=PLATFORM_SPAWN_INCLUDE_PATHS,
        syntax_only=True,
        binary_prefix="platform_spawn_resolved_plan_evidence",
    )


def test_wp14_spawn_path_uses_observable_type_name_plan_resolution_entrypoint() -> None:
    header = DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")

    assert "resolve_platform_spawn_plan_for_type_name" in header
    spawn_anchor = header.index("flecs::entity spawn(flecs::world& ecs,")
    evidence_anchor = header.index("resolve_platform_spawn_plan_for_type_name(unit_name)", spawn_anchor)
    validate_anchor = header.index(
        "validate_resolved_platform_spawn_plan(",
        evidence_anchor,
    )
    gate_anchor = header.index("if (!plan_validation.valid || !resolved_spawn_plan.admitted)", validate_anchor)
    definition_anchor = header.index("const UnitDefinition& def = it->second;", gate_anchor)
    materialization_anchor = header.index("auto e = ecs.entity()", definition_anchor)
    assert evidence_anchor < validate_anchor < gate_anchor < definition_anchor < materialization_anchor
    assert "spawn_platform" not in header


def test_wp14_resolved_spawn_plan_evidence_is_queryable_from_type_name_compat_path() -> None:
    source = textwrap.dedent(
        r"""
        #include <algorithm>
        #include <iostream>
        #include <string>
        #include "models/core/default_unit_factory.h"

        int main() {
            namespace platform = runtime::platform_capabilities;
            DefaultUnitFactory factory;

            const auto plan =
                factory.resolve_platform_spawn_plan_for_type_name("Aircraft");
            const auto validation =
                factory.validate_resolved_platform_spawn_plan_for_type_name("Aircraft");

            if (!validation.valid || !plan.admitted) {
                std::cerr << "type_name compatibility plan should validate and admit\n";
                return 1;
            }
            if (plan.source_request_kind !=
                    std::string(platform::kPlatformSpawnRequestKindTypeNameCompatibility) ||
                plan.source_type_name != "Aircraft" ||
                !plan.compatibility_path_preserved) {
                std::cerr << "type_name compatibility evidence drifted\n";
                return 1;
            }
            if (plan.materialization_strategy !=
                std::string(platform::kPlatformMaterializationStrategyFactoryCompatibility)) {
                std::cerr << "materialization strategy drifted\n";
                return 1;
            }
            if (plan.plan_id.empty() ||
                plan.capability_bundle_id.empty() ||
                plan.resolved_platform_definition_ref.empty() ||
                plan.template_evidence_ref.empty() ||
                plan.resolution_evidence_ref.empty() ||
                plan.materialization_evidence_ref.empty() ||
                plan.evidence_refs.empty() ||
                plan.resolved_capabilities.empty()) {
                std::cerr << "resolved spawn plan evidence is incomplete\n";
                return 1;
            }

            const auto has_evidence = [&](const std::string& value) {
                return std::find(plan.evidence_refs.begin(), plan.evidence_refs.end(), value) !=
                    plan.evidence_refs.end();
            };
            if (!has_evidence(plan.template_evidence_ref) ||
                !has_evidence(plan.resolution_evidence_ref) ||
                !has_evidence(plan.materialization_evidence_ref)) {
                std::cerr << "plan-level evidence refs are not inspectable\n";
                return 1;
            }

            const auto has_family = [&](std::string family) {
                return std::any_of(
                    plan.resolved_capabilities.begin(),
                    plan.resolved_capabilities.end(),
                    [&](const auto& capability) {
                        return capability.family == family &&
                            !capability.capability_id.empty() &&
                            !capability.capability_type.empty() &&
                            !capability.evidence_refs.empty();
                    });
            };
            if (!has_family(std::string(platform::kCapabilityFamilyMobility)) ||
                !has_family(std::string(platform::kCapabilityFamilySensing)) ||
                !has_family(std::string(platform::kCapabilityFamilySurvivability))) {
                std::cerr << "capability family evidence coverage drifted\n";
                return 1;
            }

            const auto missing =
                factory.resolve_platform_spawn_plan_for_type_name("Missing_Type");
            const auto missing_validation =
                factory.validate_resolved_platform_spawn_plan_for_type_name("Missing_Type");
            if (!missing_validation.valid ||
                missing.admitted ||
                !missing.compatibility_path_preserved ||
                missing.source_request_kind !=
                    std::string(platform::kPlatformSpawnRequestKindTypeNameCompatibility) ||
                missing.rejection_reason !=
                    "resolved_platform_spawn_plan_type_name_not_found") {
                std::cerr << "missing type_name rejection evidence drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_resolved_spawn_plan_air_and_naval_type_names_share_materialization_chain() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "models/core/default_unit_factory.h"

        int main() {
            namespace platform = runtime::platform_capabilities;
            DefaultUnitFactory factory;

            const auto air =
                factory.resolve_platform_spawn_plan_for_type_name("F-16C_Block50");
            const auto naval =
                factory.resolve_platform_spawn_plan_for_type_name("DDG-51_Flight_I_USS_Arleigh_Burke");

            const auto same_chain = [&](const auto& plan, const char* type_name) {
                if (!plan.admitted) {
                    std::cerr << type_name << " plan was not admitted\n";
                    return false;
                }
                if (plan.source_request_kind !=
                        std::string(platform::kPlatformSpawnRequestKindTypeNameCompatibility) ||
                    !plan.compatibility_path_preserved ||
                    plan.materialization_strategy !=
                        std::string(platform::kPlatformMaterializationStrategyFactoryCompatibility)) {
                    std::cerr << type_name << " drifted off the type_name compatibility chain\n";
                    return false;
                }
                if (plan.resolution_evidence_ref.empty() ||
                    plan.materialization_evidence_ref.empty()) {
                    std::cerr << type_name << " is missing plan-level evidence refs\n";
                    return false;
                }
                return true;
            };

            if (!same_chain(air, "F-16C_Block50") ||
                !same_chain(naval, "DDG-51_Flight_I_USS_Arleigh_Burke")) {
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
