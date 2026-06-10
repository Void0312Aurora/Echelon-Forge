from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "platform_capability_contracts.h"


def _compile_and_run(source: str):
    return compile_cpp_snippet(
        source,
        binary_prefix="platform_spawn_platform_capability_contracts",
    )


def test_wp14_platform_capability_contract_header_exists() -> None:
    assert HEADER.is_file()


def test_wp14_platform_capability_header_declares_platform_vocabulary_and_not_backend_runtime_capabilities() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for token in (
        "mobility",
        "sensing",
        "communication",
        "launching",
        "survivability",
        "command",
        "doctrine",
        "type_name_compatibility",
        "typed_platform_request",
        "factory_compatibility_materialization",
        "resolved_spawn_plan_bridge",
        "platform_capability_family_not_maintained",
        "resolved_spawn_plan_contains_unsupported_required_capability",
    ):
        assert token in header

    assert "namespace runtime::platform_capabilities" in header
    assert "RuntimeCapabilities" not in header
    assert "supports_batch_runtime" not in header


def test_wp14_platform_capability_contract_stays_header_only_and_outside_runtime_implementation_paths() -> None:
    header = HEADER.read_text(encoding="utf-8")

    for forbidden in (
        "SimulationKernel",
        "WorldBatchRuntime",
        "RuntimeFacade",
        "spawn_unit(",
        "ecs.progress",
        "flecs::world",
    ):
        assert forbidden not in header


def test_wp14_platform_capability_valid_bundle_and_resolved_plan_validate_cleanly() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/platform_capability_contracts.h"

        int main() {
            using namespace runtime::platform_capabilities;

            Capability mobility{};
            mobility.capability_id = "mobility.flight";
            mobility.family = std::string(kCapabilityFamilyMobility);
            mobility.capability_type = "fixed_wing_flight";
            mobility.implementation_ref = "airframe:F-16C_Block50";
            mobility.evidence_refs = {"content.unit_definition.airframe"};

            Capability sensing{};
            sensing.capability_id = "sensing.radar";
            sensing.family = std::string(kCapabilityFamilySensing);
            sensing.capability_type = "pulse_doppler_radar";
            sensing.implementation_ref = "sensor_ref:AN_APG_68";
            sensing.evidence_refs = {"content.unit_definition.sensor_ref"};

            CapabilityBundle bundle{};
            bundle.bundle_id = "bundle.f16c.block50";
            bundle.source_type_name = "F-16C_Block50";
            bundle.capabilities = {mobility, sensing};
            bundle.template_evidence_ref = "type_name_template:F-16C_Block50";
            bundle.evidence_refs = {
                "content.unit_definition:F-16C_Block50",
                "factory.lowering:default_unit_factory"
            };

            const auto bundle_result = validate_capability_bundle(bundle);
            if (!bundle_result.valid || bundle_result.fail_closed) {
                std::cerr << "bundle rejected: " << bundle_result.rejection_reason << "\n";
                return 1;
            }

            ResolvedPlatformSpawnPlan plan{};
            plan.plan_id = "resolved_plan.f16c.block50";
            plan.source_request_kind = std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
            plan.source_type_name = "F-16C_Block50";
            plan.capability_bundle_id = bundle.bundle_id;
            plan.resolved_platform_definition_ref = "unit_definition:F-16C_Block50";
            plan.materialization_strategy =
                std::string(kPlatformMaterializationStrategyFactoryCompatibility);
            plan.template_evidence_ref = bundle.template_evidence_ref;
            plan.resolution_evidence_ref = "resolved_bundle_from_type_name";
            plan.materialization_evidence_ref = "factory_materialization_bridge";
            plan.evidence_refs = {
                "resolved_bundle_from_type_name",
                "factory_materialization_bridge"
            };
            plan.resolved_capabilities = bundle.capabilities;
            plan.compatibility_path_preserved = true;
            plan.admitted = true;

            const auto plan_result = validate_resolved_platform_spawn_plan(plan);
            if (!plan_result.valid || plan_result.fail_closed) {
                std::cerr << "plan rejected: " << plan_result.rejection_reason << "\n";
                return 1;
            }

            const auto families = platform_capability_family_vocabulary();
            if (families.size() != 7) {
                std::cerr << "unexpected family count: " << families.size() << "\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_platform_capability_contract_fails_closed_for_invalid_family_and_bundle_shape() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/platform_capability_contracts.h"

        int main() {
            using namespace runtime::platform_capabilities;

            Capability invalid{};
            invalid.capability_id = "cap.invalid";
            invalid.family = "telepathy";
            invalid.capability_type = "magic";
            invalid.evidence_refs = {"content.invalid"};
            const auto invalid_result = validate_capability(invalid);
            if (invalid_result.valid ||
                invalid_result.rejection_reason !=
                    kPlatformCapabilityRejectionUnsupportedCapabilityFamily) {
                std::cerr << "invalid family did not fail closed\n";
                return 1;
            }

            CapabilityBundle bundle{};
            bundle.bundle_id = "bundle.empty";
            bundle.source_type_name = "Aircraft";
            bundle.template_evidence_ref = "type_name_template:Aircraft";
            bundle.evidence_refs = {"content.unit_definition:Aircraft"};
            const auto empty_bundle = validate_capability_bundle(bundle);
            if (empty_bundle.valid ||
                empty_bundle.rejection_reason !=
                    kCapabilityBundleRejectionMissingCapabilities) {
                std::cerr << "empty bundle did not fail closed\n";
                return 1;
            }

            Capability duplicate_a{};
            duplicate_a.capability_id = "duplicate";
            duplicate_a.family = std::string(kCapabilityFamilyMobility);
            duplicate_a.capability_type = "fixed_wing_flight";
            duplicate_a.evidence_refs = {"airframe"};

            Capability duplicate_b = duplicate_a;
            duplicate_b.family = std::string(kCapabilityFamilySensing);
            duplicate_b.capability_type = "radar";

            bundle.capabilities = {duplicate_a, duplicate_b};
            const auto duplicate_bundle = validate_capability_bundle(bundle);
            if (duplicate_bundle.valid ||
                duplicate_bundle.rejection_reason !=
                    kCapabilityBundleRejectionDuplicateCapabilityId) {
                std::cerr << "duplicate capability ids did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_resolved_spawn_plan_rejects_unsupported_required_capabilities_and_missing_reasons() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/platform_capability_contracts.h"

        int main() {
            using namespace runtime::platform_capabilities;

            Capability required = make_unsupported_capability(
                Capability{
                    .capability_id = "launching.vls",
                    .family = std::string(kCapabilityFamilyLaunching),
                    .capability_type = "vls_launcher",
                    .implementation_ref = "naval_weapon_system:mk41",
                    .requires_capability_ids = {},
                    .evidence_refs = {"content.unit_definition.naval_weapon_system"},
                    .required = true,
                    .supported = true,
                    .unsupported_reason = {},
                },
                kPlatformCapabilityUnsupportedEffectNotMaterialized
            );

            ResolvedPlatformSpawnPlan admitted{};
            admitted.plan_id = "resolved_plan.ddg51";
            admitted.source_request_kind =
                std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
            admitted.source_type_name = "DDG-51_Flight_I_USS_Arleigh_Burke";
            admitted.capability_bundle_id = "bundle.ddg51";
            admitted.resolved_platform_definition_ref =
                "unit_definition:DDG-51_Flight_I_USS_Arleigh_Burke";
            admitted.materialization_strategy =
                std::string(kPlatformMaterializationStrategyFactoryCompatibility);
            admitted.template_evidence_ref =
                "type_name_template:DDG-51_Flight_I_USS_Arleigh_Burke";
            admitted.resolution_evidence_ref = "resolved_bundle_from_type_name";
            admitted.materialization_evidence_ref = "factory_materialization_bridge";
            admitted.evidence_refs = {
                "resolved_bundle_from_type_name",
                "factory_materialization_bridge"
            };
            admitted.resolved_capabilities = {required};
            admitted.compatibility_path_preserved = true;
            admitted.admitted = true;

            const auto unsupported_required =
                validate_resolved_platform_spawn_plan(admitted);
            if (unsupported_required.valid ||
                unsupported_required.rejection_reason !=
                    kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability) {
                std::cerr << "unsupported required capability was admitted\n";
                return 1;
            }

            ResolvedPlatformSpawnPlan rejected{};
            rejected.plan_id = "resolved_plan.rejected";
            rejected.source_request_kind =
                std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
            rejected.source_type_name = "Aircraft";
            rejected.capability_bundle_id = "bundle.aircraft";
            rejected.compatibility_path_preserved = true;
            rejected.admitted = false;

            const auto missing_reason =
                validate_resolved_platform_spawn_plan(rejected);
            if (missing_reason.valid ||
                missing_reason.rejection_reason !=
                    kResolvedPlatformSpawnPlanRejectionMissingRejectionReason) {
                std::cerr << "rejected plan without reason did not fail closed\n";
                return 1;
            }

            rejected.rejection_reason =
                std::string(kResolvedPlatformSpawnPlanRejectionUnsupportedRequiredCapability);
            const auto rejected_ok = validate_resolved_platform_spawn_plan(rejected);
            if (!rejected_ok.valid || rejected_ok.fail_closed) {
                std::cerr << "rejected plan with stable reason should validate as a fail-closed record\n";
                return 1;
            }

            rejected.compatibility_path_preserved = false;
            const auto compatibility_broken =
                validate_resolved_platform_spawn_plan(rejected);
            if (compatibility_broken.valid ||
                compatibility_broken.rejection_reason !=
                    kResolvedPlatformSpawnPlanRejectionCompatibilityPathRequired) {
                std::cerr << "compatibility path break was not rejected\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


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
