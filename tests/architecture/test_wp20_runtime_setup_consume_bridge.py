from __future__ import annotations

import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WP20_C_DOC_CANDIDATES = (
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "wp20_public_capability_platform_composition"
    / "wp20_runtime_setup_consume_bridge_cluster_20260521.md",
    REPO_ROOT
    / "docs"
    / "task"
    / "simulation_architecture"
    / "archive"
    / "wp20_public_capability_platform_composition"
    / "wp20_runtime_setup_consume_bridge_cluster_20260521.md",
)
RUNTIME_FACADE_SOURCE = (
    REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.cpp"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _wp20_doc_text() -> str:
    for candidate in WP20_C_DOC_CANDIDATES:
        if candidate.is_file():
            return _text(candidate)
    raise AssertionError(
        "missing WP20 runtime setup consume bridge doc at active or archive path"
    )


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = (
        Path(tempfile.gettempdir())
        / f"wp20_runtime_setup_consume_bridge_test_bin_{uuid.uuid4().hex}"
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


def test_wp20_runtime_setup_consume_bridge_doc_records_validation_first_and_legacy_preservation() -> None:
    text = _wp20_doc_text()
    for required in (
        "Validation before consume",
        "Compatibility bridge",
        "Legacy preservation",
        "materialization only through the preserved `source_type_name` compatibility",
        "tests proving legacy `spawn_requests` still behave unchanged",
    ):
        assert required in text


def test_wp20_runtime_facade_apply_world_setup_contains_validation_first_typed_bridge() -> None:
    source = _text(RUNTIME_FACADE_SOURCE)

    for required in (
        "validate_typed_platform_spawn_request(request)",
        "validate_maintained_typed_platform_spawn_request(request)",
        "kTypedPlatformSpawnRejectionWorldIndexOutOfRange",
        "kTypedPlatformSpawnRejectionMaterializationFailed",
        "RuntimeFacade.apply_world_setup.explicit_legacy_compatibility_typed_platform_spawn_bridge",
        "RuntimeFacade.apply_world_setup.compatibility_type_name_materialization",
        "request.resolved_spawn_plan.source_type_name != request.source_type_name",
        "legacy_compatibility_spawn_request_from_typed_request",
        "RuntimeFacade.apply_world_setup.maintained_typed_setup",
        "spawn_typed_request_through_maintained_path",
    ):
        assert required in source


def test_wp20_runtime_setup_consume_bridge_result_contract_is_fail_closed_and_ordered() -> None:
    source = textwrap.dedent(
        r"""
        #include <algorithm>
        #include <iostream>
        #include <string>
        #include <vector>
        #include "runtime/contracts/world_batch_contracts.h"

        int main() {
            namespace platform = runtime::platform_capabilities;

            auto make_request = [](
                std::uint64_t world_index,
                std::string request_id,
                std::string source_type_name,
                bool admitted_plan
            ) {
                TypedPlatformSpawnRequest request{};
                request.world_index = world_index;
                request.side = Side::Blue;
                request.request_id = std::move(request_id);
                request.source_type_name = std::move(source_type_name);
                request.entity_name = "TypedLead";
                request.facade_evidence_refs = {
                    "BatchWorldSetupRequest.typed_platform_spawn_requests",
                    "facade:typed"
                };
                request.compatibility_path_preserved = true;

                request.capability_bundle = platform::CapabilityBundle{
                    .bundle_id = "bundle:typed",
                    .source_type_name = request.source_type_name,
                    .capabilities = {
                        platform::Capability{
                            .capability_id = "mobility:typed",
                            .family = std::string(platform::kCapabilityFamilyMobility),
                            .capability_type = "fixed_wing_flight",
                            .implementation_ref = "DefaultUnitFactory",
                            .evidence_refs = {"capability:typed"},
                        },
                    },
                    .template_evidence_ref = "template:typed",
                    .evidence_refs = {"bundle:typed"},
                    .compatibility_path_preserved = true,
                };

                request.resolved_spawn_plan = platform::ResolvedPlatformSpawnPlan{
                    .plan_id = "plan:typed",
                    .source_request_kind =
                        std::string(platform::kPlatformSpawnRequestKindTypedPlatformRequest),
                    .source_type_name = request.source_type_name,
                    .capability_bundle_id = request.capability_bundle.bundle_id,
                    .resolved_platform_definition_ref = "definition:typed",
                    .materialization_strategy =
                        std::string(platform::kPlatformMaterializationStrategyResolvedSpawnBridge),
                    .template_evidence_ref = "template:typed",
                    .resolution_evidence_ref = "resolution:typed",
                    .materialization_evidence_ref = "materialization:typed",
                    .evidence_refs = {"plan:typed"},
                    .resolved_capabilities = request.capability_bundle.capabilities,
                    .compatibility_path_preserved = true,
                    .admitted = admitted_plan,
                    .rejection_reason = admitted_plan ? "" : "resolved_plan_rejected",
                    .diagnostics_reason = admitted_plan ? "" : "plan diagnostics",
                };
                return request;
            };

            std::vector<TypedPlatformSpawnRequest> requests;
            requests.push_back(make_request(0, "typed:ok", "Aircraft", true));
            requests.push_back(make_request(7, "typed:oob", "Aircraft", true));
            requests.push_back(make_request(0, "", "Aircraft", true));
            requests.push_back(make_request(0, "typed:rejected", "Aircraft", false));

            for (std::size_t i = 0; i < requests.size(); ++i) {
                auto admission = make_typed_platform_spawn_admission(i, requests[i]);
                if (admission.request_index != i) {
                    std::cerr << "request_index ordering drifted\n";
                    return 1;
                }
            }

            const auto valid = validate_typed_platform_spawn_request(requests[0]);
            const auto invalid = validate_typed_platform_spawn_request(requests[2]);
            if (!valid.valid || invalid.valid ||
                invalid.rejection_reason !=
                    kTypedPlatformSpawnRejectionMissingRequestId) {
                std::cerr << "validation-first fail-closed contract drifted\n";
                return 1;
            }

            auto oob_admission = make_typed_platform_spawn_admission(1, requests[1]);
            oob_admission.reject(std::string(kTypedPlatformSpawnRejectionWorldIndexOutOfRange));
            auto oob_result = make_typed_platform_spawn_result(oob_admission);
            if (oob_result.request_index != 1 ||
                oob_result.rejection_reason !=
                    kTypedPlatformSpawnRejectionWorldIndexOutOfRange ||
                !oob_result.fail_closed || oob_result.admitted ||
                oob_result.materialized || oob_result.entity_id != 0U) {
                std::cerr << "world-index fail-closed contract drifted\n";
                return 1;
            }

            auto failed_materialization_admission =
                make_typed_platform_spawn_admission(0, requests[0]);
            failed_materialization_admission.admitted = true;
            auto failed_materialization_result =
                make_typed_platform_spawn_result(failed_materialization_admission);
            failed_materialization_result.admitted = true;
            failed_materialization_result.materialized = false;
            failed_materialization_result.fail_closed = true;
            failed_materialization_result.rejection_reason =
                std::string(kTypedPlatformSpawnRejectionMaterializationFailed);
            failed_materialization_result.errors.push_back("bridge returned null entity");
            if (failed_materialization_result.request_index != 0 ||
                !failed_materialization_result.admitted ||
                failed_materialization_result.materialized ||
                failed_materialization_result.entity_id != 0U ||
                failed_materialization_result.rejection_reason !=
                    kTypedPlatformSpawnRejectionMaterializationFailed ||
                failed_materialization_result.errors.size() != 1U) {
                std::cerr << "materialization failure contract drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp22_runtime_setup_contract_distinguishes_maintained_typed_setup_from_compatibility_bridge() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/world_batch_contracts.h"

        int main() {
            namespace platform = runtime::platform_capabilities;

            TypedPlatformSpawnRequest request{};
            request.world_index = 0;
            request.side = Side::Blue;
            request.request_id = "typed:bridge";
            request.source_type_name = "Aircraft";
            request.entity_name = "TypedLead";
            request.facade_evidence_refs = {
                "BatchWorldSetupRequest.typed_platform_spawn_requests",
                "facade:typed"
            };
            request.compatibility_path_preserved = true;

            request.capability_bundle = platform::CapabilityBundle{
                .bundle_id = "bundle:typed",
                .source_type_name = request.source_type_name,
                .capabilities = {
                    platform::Capability{
                        .capability_id = "mobility:typed",
                        .family = std::string(platform::kCapabilityFamilyMobility),
                        .capability_type = "fixed_wing_flight",
                        .implementation_ref = "DefaultUnitFactory",
                        .evidence_refs = {"capability:typed"},
                    },
                },
                .template_evidence_ref = "template:typed",
                .evidence_refs = {"bundle:typed"},
                .compatibility_path_preserved = true,
            };

            request.resolved_spawn_plan = platform::ResolvedPlatformSpawnPlan{
                .plan_id = "plan:typed",
                .source_request_kind =
                    std::string(platform::kPlatformSpawnRequestKindTypedPlatformRequest),
                .source_type_name = request.source_type_name,
                .capability_bundle_id = request.capability_bundle.bundle_id,
                .resolved_platform_definition_ref = "definition:typed",
                .materialization_strategy =
                    std::string(platform::kPlatformMaterializationStrategyResolvedSpawnBridge),
                .template_evidence_ref = "template:typed",
                .resolution_evidence_ref = "resolution:typed",
                .materialization_evidence_ref = "materialization:typed",
                .evidence_refs = {"plan:typed"},
                .resolved_capabilities = request.capability_bundle.capabilities,
                .compatibility_path_preserved = true,
                .admitted = true,
            };

            const auto compatibility_validation =
                validate_typed_platform_spawn_request(request);
            if (!compatibility_validation.valid || compatibility_validation.fail_closed) {
                std::cerr << "compatibility validator unexpectedly rejected bridge request\n";
                return 1;
            }

            const auto surface =
                classify_typed_platform_spawn_setup_surface(request);
            if (!surface.mixed_typed_compatibility_bridge ||
                surface.maintained_typed_setup ||
                surface.legacy_compatibility_request ||
                surface.setup_surface !=
                    kTypedPlatformSetupSurfaceMixedTypedCompatibilityBridge) {
                std::cerr << "typed setup surface classification drifted\n";
                return 1;
            }

            const auto maintained_validation =
                validate_maintained_typed_platform_spawn_request(request);
            if (maintained_validation.valid ||
                !maintained_validation.fail_closed ||
                maintained_validation.rejection_reason !=
                    kTypedPlatformSpawnRejectionMixedSetupSurface) {
                std::cerr << "maintained typed setup validator did not fail closed on compatibility bridge\n";
                return 1;
            }

            auto promoted = request;
            promoted.compatibility_path_preserved = false;
            promoted.capability_bundle.compatibility_path_preserved = false;
            promoted.resolved_spawn_plan.compatibility_path_preserved = false;
            const auto promoted_surface =
                classify_typed_platform_spawn_setup_surface(promoted);
            if (!promoted_surface.maintained_typed_setup ||
                promoted_surface.mixed_typed_compatibility_bridge ||
                promoted_surface.setup_surface !=
                    kTypedPlatformSetupSurfaceMaintainedTypedSetup) {
                std::cerr << "maintained typed setup classification drifted\n";
                return 1;
            }

            const auto promoted_validation =
                validate_maintained_typed_platform_spawn_request(promoted);
            if (!promoted_validation.valid || promoted_validation.fail_closed) {
                std::cerr << "maintained typed setup validator rejected promoted typed request\n";
                return 1;
            }

            const auto legacy_validation =
                validate_typed_platform_spawn_request(promoted);
            if (legacy_validation.valid ||
                legacy_validation.rejection_reason !=
                    kTypedPlatformSpawnRejectionCompatibilityPathRequired) {
                std::cerr << "legacy validator no longer exposes the compatibility blocker\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
