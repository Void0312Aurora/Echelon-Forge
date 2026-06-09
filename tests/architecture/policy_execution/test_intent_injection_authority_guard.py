from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "information_transform_contracts.h"
)
RUNTIME_FACADE_HEADER = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
RUNTIME_WINDOW_COORDINATOR = (
    REPO_ROOT / "src" / "runtime" / "facade" / "runtime_window_coordinator.h"
)


def _compile_and_run(source: str):
    return compile_cpp_snippet(
        source,
        binary_prefix="policy_intent_injection_authority_guard",
    )


def test_wp12_intent_injection_guard_contract_is_composed_at_information_transform_boundary() -> None:
    header = HEADER.read_text(encoding="utf-8")

    assert "MaintainedIntentInjectionRequestMetadata" in header
    assert "MaintainedActionIntentInjectionAuthorizationResult" in header
    assert "authorize_maintained_decision_belief_action_intent_injection" in header
    assert "authorize_maintained_action_intent(role, intent)" in header
    assert "validate_decision_belief_to_action_intent_transformation" in header
    assert "input_snapshot_version must match explicit DecisionBelief source_observation_versions ancestry" in header
    assert "must not masquerade as raw facade injection" in header


def test_wp12_valid_maintained_belief_to_action_intent_path_is_accepted_through_facade_compatible_metadata() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            DecisionBelief belief{};
            belief.belief_id = "belief:11";
            belief.information_state_layer = "DecisionBelief";
            belief.source_information_state.information_state_layer = "AgentObservation";
            belief.source_information_state.source_label = "facade_observation_packet";
            belief.source_information_state.maintained_status = "maintained";
            belief.source_information_state.observation_packet_ids = {"obs:11"};
            belief.source_information_state.source_observation_versions = {"global:11", "track:11"};
            belief.source_observation_versions = {"global:11", "track:11"};
            belief.memory_or_estimator_ref = "estimator:belief";
            belief.maintained_status = "maintained";

            AgentRole role{};
            role.role.role_id = "agent:2:17";
            role.role.role_type = "autopilot_controller";
            role.authority_scope.scope = "platform_control";
            role.authority_scope.world_index = 2;
            role.authority_scope.has_world_index = true;
            role.authority_scope.entity_ids = {17};
            role.information_state_source.information_state_layer = "DecisionBelief";
            role.information_state_source.source_label = "observation_derived_belief";
            role.information_state_source.maintained_status = "maintained";
            role.information_state_source.observation_packet_ids = {"belief:11"};
            role.information_state_source.source_observation_versions = {"global:11", "track:11"};
            role.decision_model_ref.kind = "policy";
            role.decision_model_ref.id = "blue-policy-v1";
            role.action_interface.kind = "PilotActionAssignmentCompat";
            role.action_interface.payload_type = "pilot_action";

            ActionIntentPacket intent{};
            intent.source_id = "policy:blue:17";
            intent.effective_time_s = 10.0;
            intent.valid_until_s = 10.5;
            intent.target.world_index = 2;
            intent.target.entity_id = 17;
            intent.action_family = "direct_control";
            intent.merge_policy = "last_write_wins";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.action_interface.payload_type = "pilot_action";
            intent.has_pilot_action = true;

            InformationTransformationEvidence evidence{};
            evidence.transformation_name =
                std::string(kCanonicalTransformationDecisionBeliefToActionIntent);
            evidence.source_layer = "DecisionBelief";
            evidence.target_layer = "ActionIntentPacket";
            evidence.maintained_status = "maintained";
            evidence.source_observation_versions = {"global:11", "track:11"};
            evidence.evidence_tokens = {"intent_injection_evidence"};

            MaintainedIntentInjectionRequestMetadata request_metadata{};
            request_metadata.source_layer = "policy";
            request_metadata.input_snapshot_version = "track:11";

            const auto result =
                authorize_maintained_decision_belief_action_intent_injection(
                    role,
                    belief,
                    intent,
                    evidence,
                    request_metadata
                );
            if (!result.authorized || !result.reason.empty() ||
                !result.authority_result.authorized ||
                !result.transformation_result.valid ||
                !result.errors.empty()) {
                std::cerr << "valid maintained path should authorize\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_missing_provenance_invalid_authority_and_illegal_shortcuts_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/information_transform_contracts.h"

        namespace {

        AgentRole make_role() {
            AgentRole role{};
            role.role.role_id = "agent:2:17";
            role.role.role_type = "autopilot_controller";
            role.authority_scope.scope = "platform_control";
            role.authority_scope.world_index = 2;
            role.authority_scope.has_world_index = true;
            role.authority_scope.entity_ids = {17};
            role.information_state_source.information_state_layer = "DecisionBelief";
            role.information_state_source.source_label = "observation_derived_belief";
            role.information_state_source.maintained_status = "maintained";
            role.information_state_source.observation_packet_ids = {"belief:11"};
            role.information_state_source.source_observation_versions = {"global:11", "track:11"};
            role.decision_model_ref.kind = "policy";
            role.decision_model_ref.id = "blue-policy-v1";
            role.action_interface.kind = "PilotActionAssignmentCompat";
            role.action_interface.payload_type = "pilot_action";
            return role;
        }

        DecisionBelief make_belief() {
            DecisionBelief belief{};
            belief.belief_id = "belief:11";
            belief.information_state_layer = "DecisionBelief";
            belief.source_information_state.information_state_layer = "AgentObservation";
            belief.source_information_state.source_label = "facade_observation_packet";
            belief.source_information_state.maintained_status = "maintained";
            belief.source_information_state.observation_packet_ids = {"obs:11"};
            belief.source_information_state.source_observation_versions = {"global:11", "track:11"};
            belief.source_observation_versions = {"global:11", "track:11"};
            belief.memory_or_estimator_ref = "estimator:belief";
            belief.maintained_status = "maintained";
            return belief;
        }

        ActionIntentPacket make_intent() {
            ActionIntentPacket intent{};
            intent.source_id = "policy:blue:17";
            intent.effective_time_s = 10.0;
            intent.valid_until_s = 10.5;
            intent.target.world_index = 2;
            intent.target.entity_id = 17;
            intent.action_family = "direct_control";
            intent.merge_policy = "last_write_wins";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.action_interface.payload_type = "pilot_action";
            intent.has_pilot_action = true;
            return intent;
        }

        runtime::information::InformationTransformationEvidence make_evidence() {
            using namespace runtime::information;
            runtime::information::InformationTransformationEvidence evidence{};
            evidence.transformation_name =
                std::string(kCanonicalTransformationDecisionBeliefToActionIntent);
            evidence.source_layer = "DecisionBelief";
            evidence.target_layer = "ActionIntentPacket";
            evidence.maintained_status = "maintained";
            evidence.source_observation_versions = {"global:11", "track:11"};
            evidence.evidence_tokens = {"intent_injection_evidence"};
            return evidence;
        }

        runtime::information::MaintainedIntentInjectionRequestMetadata make_request_metadata() {
            runtime::information::MaintainedIntentInjectionRequestMetadata metadata{};
            metadata.source_layer = "policy";
            metadata.input_snapshot_version = "track:11";
            return metadata;
        }

        bool has_error(
            const runtime::information::MaintainedActionIntentInjectionAuthorizationResult& result,
            const std::string& needle
        ) {
            for (const auto& error : result.errors) {
                if (error.find(needle) != std::string::npos) {
                    return true;
                }
            }
            return false;
        }

        }  // namespace

        int main() {
            using namespace runtime::information;

            const auto base_role = make_role();
            const auto base_belief = make_belief();
            const auto base_intent = make_intent();
            const auto base_evidence = make_evidence();
            const auto base_request = make_request_metadata();

            DecisionBelief missing_provenance = base_belief;
            missing_provenance.source_observation_versions.clear();
            missing_provenance.memory_or_estimator_ref.clear();
            const auto missing_provenance_result =
                authorize_maintained_decision_belief_action_intent_injection(
                    base_role,
                    missing_provenance,
                    base_intent,
                    base_evidence,
                    base_request
                );
            if (missing_provenance_result.authorized ||
                (missing_provenance_result.reason.find("DecisionBelief provenance") ==
                     std::string::npos &&
                 missing_provenance_result.reason.find("source_observation_versions") ==
                     std::string::npos) ||
                !has_error(missing_provenance_result, "source_observation_versions")) {
                std::cerr << "missing provenance did not fail closed\n";
                return 1;
            }

            AgentRole invalid_role = base_role;
            invalid_role.authority_scope.scope = "formation_coordination";
            const auto invalid_role_result =
                authorize_maintained_decision_belief_action_intent_injection(
                    invalid_role,
                    base_belief,
                    base_intent,
                    base_evidence,
                    base_request
                );
            if (invalid_role_result.authorized ||
                invalid_role_result.reason.find("AgentRole authority scope and action interface are incompatible") ==
                    std::string::npos ||
                invalid_role_result.authority_result.reason.find("incompatible") ==
                    std::string::npos) {
                std::cerr << "invalid role authority did not fail closed\n";
                return 1;
            }

            InformationTransformationEvidence illegal_shortcut{};
            illegal_shortcut.transformation_name =
                std::string(kDiagnosticsOnlyTransformationWorldTruthToActionIntent);
            illegal_shortcut.source_layer = "WorldTruth";
            illegal_shortcut.target_layer = "ActionIntentPacket";
            illegal_shortcut.maintained_status = "maintained";
            illegal_shortcut.source_observation_versions = {"truth:raw"};
            illegal_shortcut.evidence_tokens = {"intent_injection_evidence"};

            const auto illegal_shortcut_result =
                authorize_maintained_decision_belief_action_intent_injection(
                    base_role,
                    base_belief,
                    base_intent,
                    illegal_shortcut,
                    base_request
                );
            if (illegal_shortcut_result.authorized ||
                (illegal_shortcut_result.reason.find("source_layer does not match") ==
                     std::string::npos &&
                 illegal_shortcut_result.reason.find("diagnostics-only") ==
                     std::string::npos) ||
                !has_error(illegal_shortcut_result, "diagnostics-only")) {
                std::cerr << "illegal transformation shortcut did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_timing_snapshot_metadata_and_raw_facade_bypass_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/information_transform_contracts.h"

        namespace {

        AgentRole make_role() {
            AgentRole role{};
            role.role.role_id = "agent:2:17";
            role.role.role_type = "autopilot_controller";
            role.authority_scope.scope = "platform_control";
            role.authority_scope.world_index = 2;
            role.authority_scope.has_world_index = true;
            role.authority_scope.entity_ids = {17};
            role.information_state_source.information_state_layer = "DecisionBelief";
            role.information_state_source.source_label = "observation_derived_belief";
            role.information_state_source.maintained_status = "maintained";
            role.information_state_source.observation_packet_ids = {"belief:11"};
            role.information_state_source.source_observation_versions = {"global:11", "track:11"};
            role.decision_model_ref.kind = "policy";
            role.decision_model_ref.id = "blue-policy-v1";
            role.action_interface.kind = "PilotActionAssignmentCompat";
            role.action_interface.payload_type = "pilot_action";
            return role;
        }

        DecisionBelief make_belief() {
            DecisionBelief belief{};
            belief.belief_id = "belief:11";
            belief.information_state_layer = "DecisionBelief";
            belief.source_information_state.information_state_layer = "AgentObservation";
            belief.source_information_state.source_label = "facade_observation_packet";
            belief.source_information_state.maintained_status = "maintained";
            belief.source_information_state.observation_packet_ids = {"obs:11"};
            belief.source_information_state.source_observation_versions = {"global:11", "track:11"};
            belief.source_observation_versions = {"global:11", "track:11"};
            belief.memory_or_estimator_ref = "estimator:belief";
            belief.maintained_status = "maintained";
            return belief;
        }

        ActionIntentPacket make_intent() {
            ActionIntentPacket intent{};
            intent.source_id = "policy:blue:17";
            intent.effective_time_s = 10.0;
            intent.valid_until_s = 10.5;
            intent.target.world_index = 2;
            intent.target.entity_id = 17;
            intent.action_family = "direct_control";
            intent.merge_policy = "last_write_wins";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.action_interface.payload_type = "pilot_action";
            intent.has_pilot_action = true;
            return intent;
        }

        runtime::information::InformationTransformationEvidence make_evidence() {
            using namespace runtime::information;
            runtime::information::InformationTransformationEvidence evidence{};
            evidence.transformation_name =
                std::string(kCanonicalTransformationDecisionBeliefToActionIntent);
            evidence.source_layer = "DecisionBelief";
            evidence.target_layer = "ActionIntentPacket";
            evidence.maintained_status = "maintained";
            evidence.source_observation_versions = {"global:11", "track:11"};
            evidence.evidence_tokens = {"intent_injection_evidence"};
            return evidence;
        }

        bool has_error(
            const runtime::information::MaintainedActionIntentInjectionAuthorizationResult& result,
            const std::string& needle
        ) {
            for (const auto& error : result.errors) {
                if (error.find(needle) != std::string::npos) {
                    return true;
                }
            }
            return false;
        }

        }  // namespace

        int main() {
            using namespace runtime::information;

            const auto role = make_role();
            const auto belief = make_belief();
            const auto evidence = make_evidence();

            ActionIntentPacket invalid_timing = make_intent();
            invalid_timing.valid_until_s = 9.0;
            MaintainedIntentInjectionRequestMetadata mismatched_snapshot{};
            mismatched_snapshot.source_layer = "policy";
            mismatched_snapshot.input_snapshot_version = "obs:11";

            const auto invalid_timing_result =
                authorize_maintained_decision_belief_action_intent_injection(
                    role,
                    belief,
                    invalid_timing,
                    evidence,
                    mismatched_snapshot
                );
            if (invalid_timing_result.authorized ||
                invalid_timing_result.reason.find("input_snapshot_version") ==
                    std::string::npos ||
                !has_error(
                    invalid_timing_result,
                    "valid_until_s must be greater than or equal to effective_time_s"
                )) {
                std::cerr << "timing/snapshot metadata did not fail closed\n";
                return 1;
            }

            ActionIntentPacket bypass_intent = make_intent();
            bypass_intent.merge_policy = "append_only";
            MaintainedIntentInjectionRequestMetadata bypass_request{};
            bypass_request.source_layer = "facade";
            bypass_request.input_snapshot_version = "track:11";

            const auto bypass_result =
                authorize_maintained_decision_belief_action_intent_injection(
                    role,
                    belief,
                    bypass_intent,
                    evidence,
                    bypass_request
                );
            if (bypass_result.authorized ||
                bypass_result.reason.find("must not masquerade as raw facade injection") ==
                    std::string::npos ||
                !has_error(
                    bypass_result,
                    "merge_policy is not supported by the maintained facade-compatible injection seam"
                )) {
                std::cerr << "raw facade bypass did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_runtime_facade_does_not_gain_a_second_maintained_injection_api() -> None:
    facade_header = RUNTIME_FACADE_HEADER.read_text(encoding="utf-8")
    coordinator_header = RUNTIME_WINDOW_COORDINATOR.read_text(encoding="utf-8")

    assert "RuntimeWindowResult run_wp10_window(const RuntimeWindowRequest& request);" in facade_header
    assert "runtime_compatibility_quarantine" not in facade_header
    assert "MaintainedActionIntentInjectionAuthorizationResult" not in facade_header
    assert "authorize_maintained_decision_belief_action_intent_injection" not in facade_header
    assert "classify_runtime_window_inputs" in coordinator_header
    assert "source_layer is required" in coordinator_header
    assert "input_snapshot_version is required" in coordinator_header
