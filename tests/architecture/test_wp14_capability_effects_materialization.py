from __future__ import annotations

import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "platform_capability_contracts.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = (
        Path(tempfile.gettempdir())
        / f"wp14_capability_effects_materialization_test_bin_{uuid.uuid4().hex}"
    )
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-I",
            str(REPO_ROOT / "src"),
            "-x",
            "c++",
            "-",
            "-o",
            str(binary),
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return subprocess.run(
        [str(binary)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_wp14_effects_materialization_uses_wp14_a_family_vocabulary_only() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for token in (
        "kCapabilityFamilyMobility",
        "kCapabilityFamilySensing",
        "kCapabilityFamilyCommunication",
        "kCapabilityFamilyLaunching",
        "kCapabilityFamilySurvivability",
        "kCapabilityFamilyCommand",
        "kCapabilityFamilyDoctrine",
        "kPlatformCapabilityUnsupportedEffectNotMaterialized",
        "kPlatformCapabilityUnsupportedCompatibilityPathRequired",
        "kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability",
    ):
        assert token in header


def test_wp14_effects_materialization_contract_does_not_reuse_backend_runtime_capabilities_or_runtime_behavior_tokens() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for forbidden in (
        "RuntimeCapabilities",
        "supports_batch_runtime",
        "supports_exact_gpu_backend",
        "supports_shadow_compare",
        "fire_missile",
        "fire_naval_weapon",
        "set_mission_command",
        "step_batch",
        "ecs.progress",
        "SimulationKernel",
        "WorldBatchRuntime",
        "RuntimeFacade",
    ):
        assert forbidden not in header


def test_wp14_all_capability_families_can_be_represented_without_runtime_hooks() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string_view>
        #include <vector>
        #include "runtime/contracts/platform_capability_contracts.h"

        int main() {
            using namespace runtime::platform_capabilities;

            struct Row {
                std::string_view family;
                std::string_view capability_id;
                std::string_view capability_type;
                std::string_view implementation_ref;
                std::string_view evidence_ref;
            };

            const std::vector<Row> rows = {
                {kCapabilityFamilyMobility, "mobility.flight", "fixed_wing_flight", "airframe:F-16C_Block50", "content.unit_definition.airframe"},
                {kCapabilityFamilySensing, "sensing.radar", "pulse_doppler_radar", "sensor_ref:AN_APG_68", "content.unit_definition.sensor_ref"},
                {kCapabilityFamilyCommunication, "communication.datalink", "tactical_datalink", "data_link:link16", "content.unit_definition.data_link"},
                {kCapabilityFamilyLaunching, "launching.vls", "vls_launcher", "naval_weapon_system:mk41", "content.unit_definition.naval_weapon_system"},
                {kCapabilityFamilySurvivability, "survivability.damage", "damage_model", "damage_model:ship_hitbox", "content.unit_definition.damage_model"},
                {kCapabilityFamilyCommand, "command.mission", "mission_command_path", "command_link:compat", "content.unit_definition.command_link"},
                {kCapabilityFamilyDoctrine, "doctrine.profile", "platform_doctrine_profile", "doctrine:default", "content.unit_definition.doctrine_profile"},
            };

            for (const auto& row : rows) {
                Capability capability{};
                capability.capability_id = std::string(row.capability_id);
                capability.family = std::string(row.family);
                capability.capability_type = std::string(row.capability_type);
                capability.implementation_ref = std::string(row.implementation_ref);
                capability.evidence_refs = {std::string(row.evidence_ref)};

                const auto result = validate_capability(capability);
                if (!result.valid || result.fail_closed) {
                    std::cerr << "family failed validation: " << row.family
                              << " reason=" << result.rejection_reason << "\n";
                    return 1;
                }
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_effects_materialization_plan_can_fail_closed_without_changing_behavior_models() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/platform_capability_contracts.h"

        int main() {
            using namespace runtime::platform_capabilities;

            Capability supported{};
            supported.capability_id = "sensing.radar";
            supported.family = std::string(kCapabilityFamilySensing);
            supported.capability_type = "pulse_doppler_radar";
            supported.implementation_ref = "sensor_ref:AN_APG_68";
            supported.evidence_refs = {"content.unit_definition.sensor_ref"};

            Capability optional_unsupported = make_unsupported_capability(
                Capability{
                    .capability_id = "doctrine.experimental",
                    .family = std::string(kCapabilityFamilyDoctrine),
                    .capability_type = "experimental_doctrine_profile",
                    .implementation_ref = "doctrine:experimental",
                    .requires_capability_ids = {},
                    .evidence_refs = {"content.unit_definition.doctrine_profile"},
                    .required = false,
                    .supported = true,
                    .unsupported_reason = {},
                },
                kPlatformCapabilityUnsupportedEffectNotMaterialized
            );

            ResolvedPlatformSpawnPlan plan{};
            plan.plan_id = "resolved_plan.compat";
            plan.source_request_kind = std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
            plan.source_type_name = "F-16C_Block50";
            plan.capability_bundle_id = "bundle.f16";
            plan.resolved_platform_definition_ref = "unit_definition:F-16C_Block50";
            plan.materialization_strategy =
                std::string(kPlatformMaterializationStrategyFactoryCompatibility);
            plan.template_evidence_ref = "type_name_template:F-16C_Block50";
            plan.resolution_evidence_ref = "resolved_bundle_from_type_name";
            plan.materialization_evidence_ref = "factory_materialization_bridge";
            plan.evidence_refs = {
                "resolved_bundle_from_type_name",
                "factory_materialization_bridge"
            };
            plan.resolved_capabilities = {supported, optional_unsupported};
            plan.compatibility_path_preserved = true;
            plan.admitted = true;

            const auto accepted = validate_resolved_platform_spawn_plan(plan);
            if (!accepted.valid || accepted.fail_closed) {
                std::cerr << "optional unsupported capability should remain representable: "
                          << accepted.rejection_reason << "\n";
                return 1;
            }

            plan.resolved_capabilities[1].required = true;
            const auto rejected = validate_resolved_platform_spawn_plan(plan);
            if (rejected.valid ||
                rejected.rejection_reason !=
                    kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability) {
                std::cerr << "required unsupported capability did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
