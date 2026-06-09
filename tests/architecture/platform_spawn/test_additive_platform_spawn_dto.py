from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

WORLD_BATCH_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "world_batch_contracts.h"
FACADE_TYPES_HEADER = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
BINDINGS_SOURCE = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"


def _compile_and_run(source: str):
    return compile_cpp_snippet(
        source,
        binary_prefix="platform_spawn_additive_dto",
    )


def test_wp14_additive_spawn_dto_surface_is_declared_without_replacing_legacy_spawn() -> None:
    world_batch_header = WORLD_BATCH_HEADER.read_text(encoding="utf-8")
    facade_types_header = FACADE_TYPES_HEADER.read_text(encoding="utf-8")
    bindings_source = BINDINGS_SOURCE.read_text(encoding="utf-8")

    assert "struct WorldSpawnRequest" in world_batch_header
    assert "std::string type_name" in world_batch_header
    assert "std::vector<WorldSpawnRequest> spawn_requests" in facade_types_header

    for token in (
        "TypedPlatformSpawnRequest",
        "TypedPlatformSpawnValidationResult",
        "validate_typed_platform_spawn_request",
        "typed_platform_spawn_requests",
    ):
        assert token in world_batch_header or token in facade_types_header
        assert token in bindings_source

    for token in (
        "typed_platform_spawn_requires_capability_bundle",
        "typed_platform_spawn_requires_type_name_compatibility_path",
    ):
        assert token in world_batch_header


def test_wp14_typed_platform_spawn_request_validates_and_fails_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/world_batch_contracts.h"

        int main() {
            namespace platform = runtime::platform_capabilities;

            WorldSpawnRequest legacy{};
            legacy.type_name = "F-16C_Block50";

            TypedPlatformSpawnRequest missing{};
            const auto missing_result = validate_typed_platform_spawn_request(missing);
            if (missing_result.valid || !missing_result.fail_closed ||
                missing_result.rejection_reason !=
                    kTypedPlatformSpawnRejectionMissingRequestId) {
                std::cerr << "missing typed request did not fail closed\n";
                return 1;
            }

            TypedPlatformSpawnRequest request{};
            request.world_index = 0;
            request.side = Side::Blue;
            request.request_id = "typed-spawn:lead";
            request.source_type_name = "F-16C_Block50";
            request.entity_name = "Lead";
            request.capability_bundle =
                platform::CapabilityBundle{
                    .bundle_id = "bundle:F-16C_Block50",
                    .source_type_name = "F-16C_Block50",
                    .capabilities = {
                        platform::Capability{
                            .capability_id = "mobility:F-16C_Block50",
                            .family = std::string(platform::kCapabilityFamilyMobility),
                            .capability_type = "fixed_wing_flight",
                            .implementation_ref = "DefaultUnitFactory",
                            .evidence_refs = {"unit_definition:F-16C_Block50"},
                        },
                    },
                    .template_evidence_ref = "template:F-16C_Block50",
                    .evidence_refs = {"content:type_name:F-16C_Block50"},
                };
            request.resolved_spawn_plan =
                platform::ResolvedPlatformSpawnPlan{
                    .plan_id = "plan:typed-spawn:lead",
                    .source_request_kind =
                        std::string(platform::kPlatformSpawnRequestKindTypedPlatformRequest),
                    .source_type_name = "F-16C_Block50",
                    .capability_bundle_id = "bundle:F-16C_Block50",
                    .resolved_platform_definition_ref = "definition:F-16C_Block50",
                    .materialization_strategy =
                        std::string(platform::kPlatformMaterializationStrategyResolvedSpawnBridge),
                    .template_evidence_ref = "template:F-16C_Block50",
                    .resolution_evidence_ref = "resolver:type-name",
                    .materialization_evidence_ref = "materialization:factory-bridge",
                    .evidence_refs = {"resolved:typed-spawn:lead"},
                    .resolved_capabilities = request.capability_bundle.capabilities,
                    .compatibility_path_preserved = true,
                    .admitted = true,
                };
            request.facade_evidence_refs = {"BatchWorldSetupRequest.typed_platform_spawn_requests"};

            const auto valid_result = validate_typed_platform_spawn_request(request);
            if (!valid_result.valid || valid_result.fail_closed) {
                std::cerr << "complete typed request unexpectedly rejected: "
                          << valid_result.rejection_reason << "\n";
                return 1;
            }
            if (legacy.type_name != "F-16C_Block50") {
                std::cerr << "typed request disturbed legacy spawn surface\n";
                return 1;
            }

            auto broken = request;
            broken.resolved_spawn_plan.source_request_kind =
                std::string(platform::kPlatformSpawnRequestKindTypeNameCompatibility);
            const auto broken_result = validate_typed_platform_spawn_request(broken);
            if (broken_result.valid || broken_result.rejection_reason !=
                kTypedPlatformSpawnRejectionWrongRequestKind) {
                std::cerr << "wrong request kind did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
