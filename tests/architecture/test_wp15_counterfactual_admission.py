from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "counterfactual_replay_contracts.h"
)


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = (
        Path(tempfile.gettempdir()) / "wp15_counterfactual_admission_test_bin"
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


def test_wp15_counterfactual_admission_header_declares_request_result_and_helpers() -> None:
    text = HEADER.read_text(encoding="utf-8")

    for symbol in (
        "struct CounterfactualExperimentRequest",
        "struct CounterfactualAdmissionResult",
        "validate_counterfactual_authority_surface",
        "validate_counterfactual_experiment_request",
        "admit_counterfactual_experiment_request",
        "ordered_counterfactual_request_evidence_refs",
        "kCounterfactualAdmissionStateAdmitted",
        "kCounterfactualAdmissionStateRestoreUnsupported",
        "kCounterfactualRequestRejectionRawStateMutationForbidden",
        "kCounterfactualRequestRejectionRestoreUnsupportedBoundary",
        "kCounterfactualInterventionKindObservationWithhold",
        "kCounterfactualSourceOperatorRequest",
    ):
        assert symbol in text

    assert "generation_request.py" not in text


def test_wp15_valid_counterfactual_request_is_admitted_as_metadata_only() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include <vector>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        namespace {

        runtime::counterfactual::CounterfactualExperimentRequest make_request() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest request{};
            request.request_id = "cf:req:0001";
            request.baseline_worldline_id = "worldline:baseline";
            request.intervention_kind =
                std::string(kCounterfactualInterventionKindObservationWithhold);
            request.source = std::string(kCounterfactualSourceOperatorRequest);
            request.authority_ref = "authority:operator:blue-air";
            request.provenance_ref = "prov:counterfactual:req:0001";
            request.authority_scope.scope = std::string(kAgentAuthorityScopePlatformControl);
            request.authority_scope.world_index = 1;
            request.authority_scope.has_world_index = true;
            request.authority_scope.entity_ids = {17};
            request.authority_information_state = make_information_state_source(
                kPolicyInformationStateDecisionBelief,
                kPolicySourceLabelObservationDerivedBelief,
                kPolicyMaintainedStatusMaintained
            );
            request.authority_evidence_refs = {
                "authority_record:operator:blue-air",
                "decision_belief:counterfactual:17",
            };
            request.backend_profile_ref = "cpu_exact.reference";
            request.fidelity_profile_ref = "exact_evaluation";
            request.capability_refs = {
                "capability_bundle:f16c.block50",
                "resolved_spawn_plan:f16c.block50"
            };
            request.evidence_refs = {
                "evidence:baseline_worldline:17",
                "evidence:branch_request:17",
            };

            request.replay_envelope.replay_envelope_id = "replay:baseline:17";
            request.replay_envelope.run_id = "run:alpha";
            request.replay_envelope.episode_id = "episode:17";
            request.replay_envelope.has_deterministic_seed = true;
            request.replay_envelope.deterministic_seed = 17;
            request.replay_envelope.has_source_time = true;
            request.replay_envelope.source_time_s = 12.5;
            request.replay_envelope.snapshot_ref.snapshot_version_ref = "global:17";
            request.replay_envelope.barrier_ref.barrier_id = "window_commit";
            request.replay_envelope.barrier_ref.barrier_sequence = 4;
            request.replay_envelope.barrier_ref.barrier_detail =
                "maintained_facade_export";
            request.replay_envelope.event_order_ref.event_id = "event:17";
            request.replay_envelope.event_order_ref.producer_node_id =
                "p10.observation_export.v1";
            request.replay_envelope.facade_provenance_ref.packet_ref = "obs:17";

            request.branch_point.branch_point_id =
                make_branch_point_identity(request.replay_envelope);
            request.branch_point.replay_envelope_id =
                request.replay_envelope.replay_envelope_id;
            request.branch_point.snapshot_version_ref =
                request.replay_envelope.snapshot_ref.snapshot_version_ref;
            request.branch_point.barrier_id =
                request.replay_envelope.barrier_ref.barrier_id;
            request.branch_point.event_order_ref =
                request.replay_envelope.event_order_ref.event_id;
            request.branch_point.facade_packet_ref =
                request.replay_envelope.facade_provenance_ref.packet_ref;

            request.worldline_branch_metadata.baseline_worldline_id =
                request.baseline_worldline_id;
            request.worldline_branch_metadata.parent_worldline_id =
                request.baseline_worldline_id;
            request.worldline_branch_metadata.child_worldline_id =
                "worldline:child:0001";
            request.worldline_branch_metadata.branch_point_ref =
                request.branch_point.branch_point_id;
            request.worldline_branch_metadata.replay_envelope_ref =
                request.replay_envelope.replay_envelope_id;
            request.worldline_branch_metadata.branch_reason =
                "counterfactual_sensor_dropout_probe";
            request.worldline_branch_metadata.intervention_intent =
                "withhold_sensor_packet";
            request.worldline_branch_metadata.mutation_intent =
                std::string(kWorldlineBranchMutationIntentMetadataOnly);
            request.worldline_branch_metadata.metadata_only = true;
            request.worldline_branch_metadata.source_ref = "source:operator";
            request.worldline_branch_metadata.provenance_ref =
                "prov:branch:counterfactual:17";
            request.worldline_branch_metadata.source_information_state =
                make_information_state_source(
                    kPolicyInformationStateDecisionBelief,
                    kPolicySourceLabelObservationDerivedBelief,
                    kPolicyMaintainedStatusMaintained
                );
            request.worldline_branch_metadata.evidence_refs = {
                "evidence:obs:17",
                "evidence:branch-point:17",
            };
            request.worldline_branch_metadata.support_state =
                std::string(kWorldlineBranchSupportStateMetadataOnly);

            return request;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            const CounterfactualExperimentRequest request = make_request();
            const auto result = admit_counterfactual_experiment_request(request);
            if (!result.admitted ||
                result.admission_state != kCounterfactualAdmissionStateAdmitted ||
                result.worldline_support_state !=
                    kWorldlineBranchSupportStateMetadataOnly ||
                result.snapshot_restore_supported) {
                std::cerr << "valid metadata-only request was not admitted\n";
                return 1;
            }

            const std::vector<std::string> expected = {
                "baseline_worldline_id=worldline:baseline",
                "replay_envelope_id=replay:baseline:17",
                "branch_point_id=branch_point:replay:baseline:17:global:17:window_commit:event:17",
                "worldline_child_id=worldline:child:0001",
                "source=operator_request",
                "authority_ref=authority:operator:blue-air",
                "provenance_ref=prov:counterfactual:req:0001",
                "backend_profile_ref=cpu_exact.reference",
                "fidelity_profile_ref=exact_evaluation",
                "capability_ref=capability_bundle:f16c.block50",
                "capability_ref=resolved_spawn_plan:f16c.block50",
                "authority_evidence_ref=authority_record:operator:blue-air",
                "authority_evidence_ref=decision_belief:counterfactual:17",
                "evidence_ref=evidence:baseline_worldline:17",
                "evidence_ref=evidence:branch_request:17",
            };
            if (result.evidence_refs != expected) {
                std::cerr << "counterfactual evidence ref ordering drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_counterfactual_request_missing_required_fields_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest request{};
            const auto result = validate_counterfactual_experiment_request(request);
            if (result.valid ||
                result.rejection_reason !=
                    kCounterfactualRequestRejectionMissingRequestId) {
                std::cerr << "missing request_id did not fail first\n";
                return 1;
            }

            bool saw_baseline = false;
            bool saw_intervention = false;
            bool saw_source = false;
            bool saw_authority = false;
            bool saw_backend = false;
            bool saw_fidelity = false;
            bool saw_capability = false;
            bool saw_evidence = false;
            bool saw_replay = false;
            bool saw_branch = false;
            for (const auto& error : result.errors) {
                saw_baseline = saw_baseline ||
                    error.find("baseline_worldline_id") != std::string::npos;
                saw_intervention = saw_intervention ||
                    error.find("intervention_kind") != std::string::npos;
                saw_source = saw_source ||
                    error.find("source is required") != std::string::npos;
                saw_authority = saw_authority ||
                    error.find("authority_ref") != std::string::npos;
                saw_backend = saw_backend ||
                    error.find("backend_profile_ref") != std::string::npos;
                saw_fidelity = saw_fidelity ||
                    error.find("fidelity_profile_ref") != std::string::npos;
                saw_capability = saw_capability ||
                    error.find("capability_refs") != std::string::npos;
                saw_evidence = saw_evidence ||
                    error.find("evidence_refs") != std::string::npos;
                saw_replay = saw_replay ||
                    error.find("replay_envelope_id") != std::string::npos;
                saw_branch = saw_branch ||
                    error.find("branch_point_id") != std::string::npos;
            }

            if (!saw_baseline || !saw_intervention || !saw_source ||
                !saw_authority || !saw_backend || !saw_fidelity ||
                !saw_capability || !saw_evidence || !saw_replay || !saw_branch) {
                std::cerr << "missing-field coverage incomplete\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_counterfactual_request_rejects_raw_mutation_and_invalid_authority_surface() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        namespace {

        runtime::counterfactual::CounterfactualExperimentRequest make_request() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest request{};
            request.request_id = "cf:req:raw";
            request.baseline_worldline_id = "worldline:baseline";
            request.intervention_kind =
                std::string(kCounterfactualInterventionKindPolicySubstitution);
            request.source = std::string(kCounterfactualSourceAnalystRequest);
            request.authority_ref = "authority:analyst";
            request.provenance_ref = "prov:analyst";
            request.authority_scope.scope = std::string(kAgentAuthorityScopePlatformControl);
            request.authority_scope.world_index = 1;
            request.authority_scope.has_world_index = true;
            request.authority_scope.entity_ids = {7};
            request.authority_information_state = make_information_state_source(
                kPolicyInformationStateDecisionBelief,
                kPolicySourceLabelObservationDerivedBelief,
                kPolicyMaintainedStatusMaintained
            );
            request.authority_evidence_refs = {"authority_record:analyst"};
            request.backend_profile_ref = "cpu_exact.reference";
            request.fidelity_profile_ref = "exact_evaluation";
            request.capability_refs = {"capability_bundle:test"};
            request.evidence_refs = {"evidence:req"};

            request.replay_envelope.replay_envelope_id = "replay:raw";
            request.replay_envelope.run_id = "run:raw";
            request.replay_envelope.episode_id = "episode:raw";
            request.replay_envelope.has_deterministic_seed = true;
            request.replay_envelope.deterministic_seed = 1;
            request.replay_envelope.has_source_time = true;
            request.replay_envelope.source_time_s = 1.0;
            request.replay_envelope.snapshot_ref.snapshot_version_ref = "global:1";
            request.replay_envelope.barrier_ref.barrier_id = "window_commit";
            request.replay_envelope.barrier_ref.barrier_detail =
                "maintained_facade_export";
            request.replay_envelope.event_order_ref.event_id = "event:1";
            request.replay_envelope.event_order_ref.producer_node_id =
                "p10.observation_export.v1";
            request.replay_envelope.facade_provenance_ref.packet_ref = "obs:1";

            request.branch_point.branch_point_id =
                make_branch_point_identity(request.replay_envelope);
            request.branch_point.replay_envelope_id =
                request.replay_envelope.replay_envelope_id;
            request.branch_point.snapshot_version_ref = "global:1";
            request.branch_point.barrier_id = "window_commit";
            request.branch_point.event_order_ref = "event:1";
            request.branch_point.facade_packet_ref = "obs:1";

            request.worldline_branch_metadata.baseline_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.parent_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.child_worldline_id =
                "worldline:child:raw";
            request.worldline_branch_metadata.branch_point_ref =
                request.branch_point.branch_point_id;
            request.worldline_branch_metadata.replay_envelope_ref =
                request.replay_envelope.replay_envelope_id;
            request.worldline_branch_metadata.branch_reason = "test";
            request.worldline_branch_metadata.intervention_intent = "substitute_policy";
            request.worldline_branch_metadata.source_ref = "source:analyst";
            request.worldline_branch_metadata.provenance_ref = "prov:branch";
            request.worldline_branch_metadata.evidence_refs = {"evidence:branch"};
            request.worldline_branch_metadata.support_state =
                std::string(kWorldlineBranchSupportStateMetadataOnly);

            return request;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest raw = make_request();
            raw.requests_authoritative_state_mutation = true;
            raw.intervention_kind =
                std::string(
                    kCounterfactualInterventionKindRawAuthoritativeStateMutation
                );
            raw.worldline_branch_metadata.requests_authoritative_state_mutation = true;
            raw.worldline_branch_metadata.mutation_intent =
                std::string(
                    kWorldlineBranchMutationIntentRawAuthoritativeStateMutation
                );
            const auto raw_result = admit_counterfactual_experiment_request(raw);
            if (raw_result.admitted ||
                raw_result.rejection_reason !=
                    kCounterfactualRequestRejectionRawStateMutationForbidden) {
                std::cerr << "raw authoritative state mutation was not rejected\n";
                return 1;
            }

            CounterfactualExperimentRequest invalid_authority = make_request();
            invalid_authority.authority_scope.entity_ids.clear();
            const auto invalid_scope =
                validate_counterfactual_authority_surface(invalid_authority);
            if (invalid_scope.valid ||
                invalid_scope.rejection_reason !=
                    kCounterfactualRequestRejectionInvalidAuthorityScope) {
                std::cerr << "invalid authority scope was not rejected\n";
                return 1;
            }

            invalid_authority = make_request();
            invalid_authority.authority_information_state.maintained_status =
                std::string(kPolicyMaintainedStatusDiagnosticsOnly);
            const auto invalid_source =
                validate_counterfactual_authority_surface(invalid_authority);
            if (invalid_source.valid ||
                invalid_source.rejection_reason !=
                    kCounterfactualRequestRejectionInvalidAuthoritySource) {
                std::cerr << "invalid authority provenance source was not rejected\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_counterfactual_request_surfaces_restore_unsupported_without_claiming_execution() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        namespace {

        runtime::counterfactual::CounterfactualExperimentRequest make_request() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest request{};
            request.request_id = "cf:req:restore";
            request.baseline_worldline_id = "worldline:baseline";
            request.intervention_kind =
                std::string(kCounterfactualInterventionKindCommandVariant);
            request.source = std::string(kCounterfactualSourceExperimentPlan);
            request.authority_ref = "authority:planner";
            request.provenance_ref = "prov:planner";
            request.authority_scope.scope = std::string(kAgentAuthorityScopeMissionCommand);
            request.authority_scope.world_index = 1;
            request.authority_scope.has_world_index = true;
            request.authority_scope.entity_ids = {9};
            request.authority_information_state = make_information_state_source(
                kPolicyInformationStateDecisionBelief,
                kPolicySourceLabelObservationDerivedBelief,
                kPolicyMaintainedStatusMaintained
            );
            request.authority_evidence_refs = {"authority_record:planner"};
            request.backend_profile_ref = "cpu_exact.reference";
            request.fidelity_profile_ref = "exact_evaluation";
            request.capability_refs = {"resolved_spawn_plan:mission-command"};
            request.evidence_refs = {"evidence:req:restore"};
            request.requests_executable_branch = true;

            request.replay_envelope.replay_envelope_id = "replay:restore";
            request.replay_envelope.run_id = "run:restore";
            request.replay_envelope.episode_id = "episode:restore";
            request.replay_envelope.has_deterministic_seed = true;
            request.replay_envelope.deterministic_seed = 19;
            request.replay_envelope.has_source_time = true;
            request.replay_envelope.source_time_s = 2.0;
            request.replay_envelope.snapshot_ref.snapshot_version_ref = "global:19";
            request.replay_envelope.barrier_ref.barrier_id = "window_commit";
            request.replay_envelope.barrier_ref.barrier_detail =
                "maintained_facade_export";
            request.replay_envelope.event_order_ref.event_id = "event:19";
            request.replay_envelope.event_order_ref.producer_node_id =
                "p10.observation_export.v1";
            request.replay_envelope.facade_provenance_ref.packet_ref = "obs:19";

            request.branch_point.branch_point_id =
                make_branch_point_identity(request.replay_envelope);
            request.branch_point.replay_envelope_id =
                request.replay_envelope.replay_envelope_id;
            request.branch_point.snapshot_version_ref = "global:19";
            request.branch_point.barrier_id = "window_commit";
            request.branch_point.event_order_ref = "event:19";
            request.branch_point.facade_packet_ref = "obs:19";

            request.worldline_branch_metadata.baseline_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.parent_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.child_worldline_id =
                "worldline:child:restore";
            request.worldline_branch_metadata.branch_point_ref =
                request.branch_point.branch_point_id;
            request.worldline_branch_metadata.replay_envelope_ref =
                request.replay_envelope.replay_envelope_id;
            request.worldline_branch_metadata.branch_reason = "compare_command_variant";
            request.worldline_branch_metadata.intervention_intent = "alternate_mission_command";
            request.worldline_branch_metadata.source_ref = "source:planner";
            request.worldline_branch_metadata.provenance_ref = "prov:branch:restore";
            request.worldline_branch_metadata.evidence_refs = {"evidence:branch:restore"};
            request.worldline_branch_metadata.support_state =
                std::string(kWorldlineBranchSupportStateMetadataOnly);

            return request;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            const auto request = make_request();
            const auto result = admit_counterfactual_experiment_request(request);
            if (result.admitted ||
                result.admission_state !=
                    kCounterfactualAdmissionStateRestoreUnsupported ||
                result.worldline_support_state !=
                    kWorldlineBranchSupportStateRestoreUnsupported ||
                result.rejection_reason !=
                    kCounterfactualRequestRejectionRestoreUnsupportedBoundary) {
                std::cerr << "restore unsupported boundary was not surfaced\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_counterfactual_request_rejects_invalid_refs_without_promoting_support() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        namespace {

        runtime::counterfactual::CounterfactualExperimentRequest make_request() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest request{};
            request.request_id = "cf:req:refs";
            request.baseline_worldline_id = "worldline:baseline";
            request.intervention_kind =
                std::string(kCounterfactualInterventionKindSpawnVariantRequest);
            request.source = std::string(kCounterfactualSourceCounterfactualBranch);
            request.authority_ref = "authority:branch";
            request.provenance_ref = "prov:branch";
            request.authority_scope.scope =
                std::string(kAgentAuthorityScopeFormationCoordination);
            request.authority_scope.world_index = 1;
            request.authority_scope.has_world_index = true;
            request.authority_scope.roster_id = "blue-section";
            request.authority_information_state = make_information_state_source(
                kPolicyInformationStateDecisionBelief,
                kPolicySourceLabelObservationDerivedBelief,
                kPolicyMaintainedStatusMaintained
            );
            request.authority_evidence_refs = {"authority_record:branch"};
            request.backend_profile_ref = "cpu_exact.reference";
            request.fidelity_profile_ref = "exact_evaluation";
            request.capability_refs = {"capability_bundle:test"};
            request.evidence_refs = {"evidence:req:refs"};

            request.replay_envelope.replay_envelope_id = "replay:refs";
            request.replay_envelope.run_id = "run:refs";
            request.replay_envelope.episode_id = "episode:refs";
            request.replay_envelope.has_deterministic_seed = true;
            request.replay_envelope.deterministic_seed = 23;
            request.replay_envelope.has_source_time = true;
            request.replay_envelope.source_time_s = 3.0;
            request.replay_envelope.snapshot_ref.snapshot_version_ref = "global:23";
            request.replay_envelope.barrier_ref.barrier_id = "window_commit";
            request.replay_envelope.barrier_ref.barrier_detail =
                "maintained_facade_export";
            request.replay_envelope.event_order_ref.event_id = "event:23";
            request.replay_envelope.event_order_ref.producer_node_id =
                "p10.observation_export.v1";
            request.replay_envelope.facade_provenance_ref.packet_ref = "obs:23";

            request.branch_point.branch_point_id =
                make_branch_point_identity(request.replay_envelope);
            request.branch_point.replay_envelope_id =
                request.replay_envelope.replay_envelope_id;
            request.branch_point.snapshot_version_ref = "global:23";
            request.branch_point.barrier_id = "window_commit";
            request.branch_point.event_order_ref = "event:23";
            request.branch_point.facade_packet_ref = "obs:23";

            request.worldline_branch_metadata.baseline_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.parent_worldline_id =
                "worldline:baseline";
            request.worldline_branch_metadata.child_worldline_id =
                "worldline:child:refs";
            request.worldline_branch_metadata.branch_point_ref =
                request.branch_point.branch_point_id;
            request.worldline_branch_metadata.replay_envelope_ref =
                request.replay_envelope.replay_envelope_id;
            request.worldline_branch_metadata.branch_reason = "spawn_variant_probe";
            request.worldline_branch_metadata.intervention_intent = "spawn_variant_request";
            request.worldline_branch_metadata.source_ref = "source:branch";
            request.worldline_branch_metadata.provenance_ref = "prov:worldline:refs";
            request.worldline_branch_metadata.evidence_refs = {"evidence:branch:refs"};
            request.worldline_branch_metadata.support_state =
                std::string(kWorldlineBranchSupportStateMetadataOnly);

            return request;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            CounterfactualExperimentRequest missing_backend = make_request();
            missing_backend.backend_profile_ref = "backend.missing";
            const auto backend_result =
                admit_counterfactual_experiment_request(missing_backend);
            if (backend_result.admitted ||
                backend_result.rejection_reason !=
                    kCounterfactualRequestRejectionUnsupportedBackendProfileRef) {
                std::cerr << "missing backend ref did not fail closed\n";
                return 1;
            }

            CounterfactualExperimentRequest invalid_fidelity = make_request();
            invalid_fidelity.fidelity_profile_ref = "fast_training";
            const auto fidelity_result =
                admit_counterfactual_experiment_request(invalid_fidelity);
            if (fidelity_result.admitted ||
                fidelity_result.rejection_reason !=
                    kCounterfactualRequestRejectionUnsupportedFidelityProfileRef) {
                std::cerr << "unsupported fidelity ref did not fail closed\n";
                return 1;
            }

            CounterfactualExperimentRequest invalid_capability = make_request();
            invalid_capability.capability_refs = {"capability:test"};
            const auto capability_result =
                admit_counterfactual_experiment_request(invalid_capability);
            if (capability_result.admitted ||
                capability_result.rejection_reason !=
                    kCounterfactualRequestRejectionUnsupportedCapabilityRef) {
                std::cerr << "invalid capability ref did not fail closed\n";
                return 1;
            }

            CounterfactualExperimentRequest preclaimed_support = make_request();
            preclaimed_support.worldline_branch_metadata.support_state =
                std::string(kWorldlineBranchSupportStateAdmitted);
            const auto support_result =
                admit_counterfactual_experiment_request(preclaimed_support);
            if (support_result.admitted ||
                support_result.rejection_reason !=
                    kCounterfactualRequestRejectionWorldlineSupportStatePreclaimForbidden) {
                std::cerr << "support preclaim was not rejected\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
