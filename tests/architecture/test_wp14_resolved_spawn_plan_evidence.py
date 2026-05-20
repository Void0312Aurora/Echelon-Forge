from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UNIT_FACTORY_HEADER = REPO_ROOT / "src" / "models" / "core" / "default_unit_factory.h"
SPDLOG_INCLUDE = REPO_ROOT / "build-local-win" / "_deps" / "spdlog-src" / "include"
FLECS_INCLUDE = REPO_ROOT / "build-local-win" / "_deps" / "flecs-src" / "include"
NLOHMANN_JSON_INCLUDE = REPO_ROOT / "build-local-win" / "_deps" / "nlohmann_json-src" / "include"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-fsyntax-only",
            "-I",
            str(REPO_ROOT / "src"),
            "-I",
            str(SPDLOG_INCLUDE),
            "-I",
            str(FLECS_INCLUDE),
            "-I",
            str(NLOHMANN_JSON_INCLUDE),
            "-x",
            "c++",
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return compile_result


def test_wp14_spawn_path_uses_observable_type_name_plan_resolution_entrypoint() -> None:
    header = DEFAULT_UNIT_FACTORY_HEADER.read_text(encoding="utf-8")

    assert "resolve_platform_spawn_plan_for_type_name" in header
    spawn_anchor = header.index("flecs::entity spawn(flecs::world& ecs,")
    definition_anchor = header.index("const UnitDefinition& def = it->second;", spawn_anchor)
    evidence_anchor = header.index("resolve_platform_spawn_plan_for_type_name(unit_name)", definition_anchor)
    materialization_anchor = header.index("auto e = ecs.entity()", definition_anchor)
    assert definition_anchor < evidence_anchor < materialization_anchor
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
