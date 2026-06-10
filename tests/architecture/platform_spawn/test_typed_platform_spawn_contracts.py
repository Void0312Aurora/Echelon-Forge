from __future__ import annotations

import re
import textwrap
from pathlib import Path

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

WORLD_BATCH_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "world_batch_contracts.h"
FACADE_TYPES_HEADER = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
BINDINGS_SOURCE = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"
WP20_B_DOC_CANDIDATES = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp20_public_capability_platform_composition"
    / "wp20_public_typed_platform_spawn_contract_cluster_20260521.md",
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "archive"
    / "wp20_public_capability_platform_composition"
    / "wp20_public_typed_platform_spawn_contract_cluster_20260521.md",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _wp20_doc_text() -> str:
    for candidate in WP20_B_DOC_CANDIDATES:
        if candidate.is_file():
            return _text(candidate)
    raise AssertionError(
        "missing WP20 public typed platform spawn contract doc at active or archive path"
    )


def _struct_body(header: str, struct_name: str) -> str:
    pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
    match = re.search(pattern, header, flags=re.DOTALL)
    assert match is not None, f"{struct_name} missing from {WORLD_BATCH_HEADER}"
    return match.group("body")


def _compile_and_run(source: str):
    return compile_cpp_snippet(
        source,
        binary_prefix="platform_spawn_public_typed_contract",
    )


def test_wp20_typed_platform_spawn_result_surface_is_additive_and_precise() -> None:
    world_batch_header = _text(WORLD_BATCH_HEADER)
    facade_types_header = _text(FACADE_TYPES_HEADER)

    for token in (
        "TypedPlatformSpawnAdmission",
        "TypedPlatformSpawnResult",
        "collect_typed_platform_spawn_evidence_refs",
        "make_typed_platform_spawn_admission",
        "make_typed_platform_spawn_result",
        "typed_platform_spawn_world_index_out_of_range",
        "typed_platform_spawn_materialization_failed",
    ):
        assert token in world_batch_header

    admission = _struct_body(world_batch_header, "TypedPlatformSpawnAdmission")
    result = _struct_body(world_batch_header, "TypedPlatformSpawnResult")

    for field in (
        "request_index",
        "world_index",
        "admitted",
        "fail_closed",
        "request_id",
        "source_type_name",
        "plan_id",
        "capability_bundle_id",
        "rejection_reason",
        "errors",
        "evidence_refs",
    ):
        assert field in admission

    for field in (
        "request_index",
        "world_index",
        "entity_id",
        "admitted",
        "materialized",
        "fail_closed",
        "request_id",
        "source_type_name",
        "plan_id",
        "capability_bundle_id",
        "rejection_reason",
        "errors",
        "evidence_refs",
    ):
        assert field in result

    setup_result = _struct_body(facade_types_header, "BatchWorldSetupResult")
    assert "std::vector<std::uint64_t> entity_ids;" in setup_result
    assert "std::vector<TypedPlatformSpawnResult> typed_platform_spawn_results;" in setup_result


def test_wp20_typed_platform_spawn_contract_doc_records_ordering_and_cd_handoff() -> None:
    text = _wp20_doc_text()

    for required in (
        "## Ordering Rule",
        "typed_platform_spawn_results[i].request_index == i",
        "`entity_ids` remains the legacy result channel",
        "## Exact Interface For C/D",
        "TypedPlatformSpawnAdmission",
        "TypedPlatformSpawnResult",
        "typed_platform_spawn_world_index_out_of_range",
        "typed_platform_spawn_materialization_failed",
    ):
        assert required in text


def test_wp20_typed_platform_spawn_helpers_preserve_seeded_identity_and_evidence_order() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include <vector>
        #include "runtime/contracts/world_batch_contracts.h"

        int main() {
            namespace platform = runtime::platform_capabilities;

            TypedPlatformSpawnRequest request{};
            request.world_index = 3;
            request.request_id = "typed-spawn:alpha";
            request.source_type_name = "F-16C_Block50";
            request.facade_evidence_refs = {
                "facade:req",
                "shared:evidence",
                "facade:req"
            };
            request.capability_bundle = platform::CapabilityBundle{
                .bundle_id = "bundle:F-16C_Block50",
                .source_type_name = "F-16C_Block50",
                .capabilities = {
                    platform::Capability{
                        .capability_id = "mobility:F-16C_Block50",
                        .family = std::string(platform::kCapabilityFamilyMobility),
                        .capability_type = "fixed_wing_flight",
                        .implementation_ref = "DefaultUnitFactory",
                        .evidence_refs = {"capability:evidence"},
                    },
                },
                .template_evidence_ref = "template:F-16C_Block50",
                .evidence_refs = {"shared:evidence", "bundle:evidence"},
            };
            request.resolved_spawn_plan = platform::ResolvedPlatformSpawnPlan{
                .plan_id = "plan:typed-spawn:alpha",
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
                .evidence_refs = {"plan:evidence", "shared:evidence"},
                .resolved_capabilities = request.capability_bundle.capabilities,
                .compatibility_path_preserved = true,
                .admitted = true,
            };

            const auto evidence = collect_typed_platform_spawn_evidence_refs(request);
            const std::vector<std::string> expected_evidence = {
                "facade:req",
                "shared:evidence",
                "template:F-16C_Block50",
                "bundle:evidence",
                "resolver:type-name",
                "materialization:factory-bridge",
                "plan:evidence",
            };
            if (evidence != expected_evidence) {
                std::cerr << "evidence ordering drifted\n";
                return 1;
            }

            auto admission = make_typed_platform_spawn_admission(7, request);
            if (admission.request_index != 7 || admission.world_index != 3 ||
                admission.request_id != "typed-spawn:alpha" ||
                admission.source_type_name != "F-16C_Block50" ||
                admission.plan_id != "plan:typed-spawn:alpha" ||
                admission.capability_bundle_id != "bundle:F-16C_Block50" ||
                admission.admitted || admission.fail_closed ||
                !admission.rejection_reason.empty() || !admission.errors.empty() ||
                admission.evidence_refs != expected_evidence) {
                std::cerr << "admission seed shape drifted\n";
                return 1;
            }

            admission.admitted = true;
            auto result = make_typed_platform_spawn_result(admission);
            if (result.request_index != 7 || result.world_index != 3 ||
                result.request_id != "typed-spawn:alpha" ||
                result.source_type_name != "F-16C_Block50" ||
                result.plan_id != "plan:typed-spawn:alpha" ||
                result.capability_bundle_id != "bundle:F-16C_Block50" ||
                !result.admitted || result.materialized || result.fail_closed ||
                result.entity_id != 0 || result.evidence_refs != expected_evidence) {
                std::cerr << "result seed shape drifted\n";
                return 1;
            }

            result.reject(std::string(kTypedPlatformSpawnRejectionMaterializationFailed));
            result.add_error("bridge returned null entity");
            if (result.admitted || result.materialized || !result.fail_closed ||
                result.rejection_reason !=
                    kTypedPlatformSpawnRejectionMaterializationFailed ||
                result.errors.size() != 1U) {
                std::cerr << "result reject helper drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp14_additive_spawn_dto_surface_is_declared_without_replacing_legacy_spawn() -> None:
    world_batch_header = _text(WORLD_BATCH_HEADER)
    facade_types_header = _text(FACADE_TYPES_HEADER)
    bindings_source = _text(BINDINGS_SOURCE)

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
