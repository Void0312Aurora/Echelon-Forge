from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "information_transform_contracts.h"
)
POLICY_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"


def _compile_and_run(source: str) -> subprocess.CompletedProcess[str]:
    binary = "/tmp/wp12_information_transformation_surface_test_bin"
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
            binary,
        ],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    return subprocess.run(
        [binary],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_wp12_information_transformation_header_exists_at_stable_runtime_contract_path() -> None:
    assert HEADER.is_file()


def test_wp12_information_transformation_header_reuses_policy_vocabulary_without_engine_dependencies() -> None:
    header = HEADER.read_text(encoding="utf-8")
    policy = POLICY_HEADER.read_text(encoding="utf-8")

    assert '#include "runtime/contracts/policy_contracts.h"' in header
    assert "core/engine" not in header
    assert "scheduler" not in header.lower()
    assert "kPolicyInformationStateWorldTruth" in policy
    for token in (
        "kCanonicalTransformationWorldTruthToSensedState",
        "kCanonicalTransformationSensedStateToTrackState",
        "kCanonicalTransformationTrackStateToSharedTacticalPicture",
        "kCanonicalTransformationSharedTacticalPictureToAgentObservation",
        "kCanonicalTransformationAgentObservationToDecisionBelief",
        "kCanonicalTransformationDecisionBeliefToActionIntent",
        "kDiagnosticsOnlyTransformationWorldTruthToActionIntent",
        "InformationTransformationSpec",
        "InformationTransformationEvidence",
        "validate_information_transformation_evidence",
        "validate_information_source_transformation",
        "validate_decision_belief_transformation",
        "validate_decision_belief_to_action_intent_transformation",
    ):
        assert token in header


def test_wp12_canonical_transformation_vocabulary_is_machine_checkable() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            if (kCanonicalInformationTransformations.size() != 6) {
                std::cerr << "unexpected canonical transformation count\n";
                return 1;
            }
            if (std::string(kCanonicalInformationTransformations.front().source_layer) !=
                    "WorldTruth" ||
                std::string(kCanonicalInformationTransformations.front().target_layer) !=
                    "SensedState") {
                std::cerr << "first canonical transformation drifted\n";
                return 1;
            }
            if (std::string(kCanonicalInformationTransformations.back().source_layer) !=
                    "DecisionBelief" ||
                std::string(kCanonicalInformationTransformations.back().target_layer) !=
                    "ActionIntentPacket") {
                std::cerr << "last canonical transformation drifted\n";
                return 1;
            }
            if (!is_canonical_information_transformation_name(
                    kCanonicalTransformationAgentObservationToDecisionBelief)) {
                std::cerr << "canonical transformation lookup drifted\n";
                return 1;
            }
            const auto* spec = find_information_transformation_spec(
                kCanonicalTransformationSharedTacticalPictureToAgentObservation);
            if (spec == nullptr ||
                spec->source_layer != "SharedTacticalPicture" ||
                spec->target_layer != "AgentObservation" ||
                spec->evidence_requirement != "observation_view_evidence") {
                std::cerr << "spec lookup drifted\n";
                return 1;
            }
            const auto* diagnostics = find_information_transformation_spec(
                kDiagnosticsOnlyTransformationWorldTruthToActionIntent);
            if (diagnostics == nullptr ||
                diagnostics->maintained_allowed ||
                !diagnostics->diagnostics_only_allowed) {
                std::cerr << "diagnostics-only shortcut drifted\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_selected_slice_maintained_packet_belief_and_intent_can_name_legal_transformation_steps() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            InformationStateSource observation{};
            observation.information_state_layer = "AgentObservation";
            observation.source_label = "facade_observation_packet";
            observation.maintained_status = "maintained";
            observation.observation_packet_ids = {"obs:11"};
            observation.source_observation_versions = {"stp:11"};

            InformationTransformationEvidence stp_to_ao{};
            stp_to_ao.transformation_name =
                std::string(kCanonicalTransformationSharedTacticalPictureToAgentObservation);
            stp_to_ao.source_layer = "SharedTacticalPicture";
            stp_to_ao.target_layer = "AgentObservation";
            stp_to_ao.maintained_status = "maintained";
            stp_to_ao.source_observation_versions = {"stp:11"};
            stp_to_ao.evidence_tokens = {"observation_view_evidence"};

            const auto packet_result = validate_information_source_transformation(
                observation,
                stp_to_ao);
            if (!packet_result.valid) {
                std::cerr << "stp_to_ao should validate\n";
                return 1;
            }

            DecisionBelief belief{};
            belief.belief_id = "belief:11";
            belief.information_state_layer = "DecisionBelief";
            belief.source_information_state = observation;
            belief.source_observation_versions = {"obs:11"};
            belief.memory_or_estimator_ref = "estimator:belief";
            belief.maintained_status = "maintained";

            InformationTransformationEvidence ao_to_db{};
            ao_to_db.transformation_name =
                std::string(kCanonicalTransformationAgentObservationToDecisionBelief);
            ao_to_db.source_layer = "AgentObservation";
            ao_to_db.target_layer = "DecisionBelief";
            ao_to_db.maintained_status = "maintained";
            ao_to_db.source_observation_versions = {"obs:11"};
            ao_to_db.evidence_tokens = {"decision_inference_evidence"};

            const auto belief_result = validate_decision_belief_transformation(
                belief,
                ao_to_db);
            if (!belief_result.valid) {
                std::cerr << "ao_to_db should validate\n";
                return 1;
            }

            ActionIntentPacket intent{};
            intent.source_id = "policy:blue:11";
            intent.action_family = "direct_control";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.has_pilot_action = true;

            InformationTransformationEvidence db_to_ai{};
            db_to_ai.transformation_name =
                std::string(kCanonicalTransformationDecisionBeliefToActionIntent);
            db_to_ai.source_layer = "DecisionBelief";
            db_to_ai.target_layer = "ActionIntentPacket";
            db_to_ai.maintained_status = "maintained";
            db_to_ai.source_observation_versions = {"belief:11"};
            db_to_ai.evidence_tokens = {"intent_injection_evidence"};

            const auto intent_result =
                validate_decision_belief_to_action_intent_transformation(
                    belief,
                    intent,
                    db_to_ai);
            if (!intent_result.valid) {
                std::cerr << "db_to_ai should validate\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_missing_transformation_metadata_and_unknown_names_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            InformationTransformationEvidence missing{};
            missing.transformation_name =
                std::string(kCanonicalTransformationAgentObservationToDecisionBelief);
            missing.source_layer = "AgentObservation";
            missing.target_layer = "DecisionBelief";
            missing.maintained_status = "maintained";

            const auto missing_result =
                validate_information_transformation_evidence(missing);
            if (missing_result.valid) {
                std::cerr << "missing metadata unexpectedly passed\n";
                return 1;
            }

            bool saw_versions = false;
            bool saw_evidence = false;
            for (const auto& error : missing_result.errors) {
                saw_versions =
                    saw_versions ||
                    error.find("source_observation_versions") != std::string::npos;
                saw_evidence =
                    saw_evidence ||
                    error.find("evidence_tokens") != std::string::npos;
            }
            if (!saw_versions || !saw_evidence) {
                std::cerr << "missing metadata did not fail closed as expected\n";
                return 1;
            }

            InformationTransformationEvidence unknown{};
            unknown.transformation_name = "made_up_transform.v9";
            unknown.source_layer = "TrackState";
            unknown.target_layer = "DecisionBelief";
            unknown.maintained_status = "maintained";
            unknown.source_observation_versions = {"track:7"};
            unknown.evidence_tokens = {"decision_inference_evidence"};

            const auto unknown_result =
                validate_information_transformation_evidence(unknown);
            if (unknown_result.valid) {
                std::cerr << "unknown transformation unexpectedly passed\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_illegal_world_truth_to_action_intent_maintained_shortcut_fails_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            InformationStateSource truth{};
            truth.information_state_layer = "WorldTruth";
            truth.source_label = "world_truth_diagnostics";
            truth.maintained_status = "maintained";
            truth.source_observation_versions = {"truth:5"};

            ActionIntentPacket intent{};
            intent.source_id = "oracle:5";
            intent.action_family = "direct_control";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.has_pilot_action = true;

            InformationTransformationEvidence shortcut{};
            shortcut.transformation_name =
                std::string(kDiagnosticsOnlyTransformationWorldTruthToActionIntent);
            shortcut.source_layer = "WorldTruth";
            shortcut.target_layer = "ActionIntentPacket";
            shortcut.maintained_status = "maintained";
            shortcut.source_observation_versions = {"truth:5"};
            shortcut.evidence_tokens = {"intent_injection_evidence"};

            const auto result =
                validate_information_source_to_action_intent_transformation(
                    truth,
                    intent,
                    shortcut);
            if (result.valid) {
                std::cerr << "maintained world-truth shortcut unexpectedly passed\n";
                return 1;
            }
            bool saw_diagnostics_only = false;
            for (const auto& error : result.errors) {
                saw_diagnostics_only =
                    saw_diagnostics_only ||
                    error.find("diagnostics-only") != std::string::npos ||
                    error.find("diagnostics_only") != std::string::npos;
            }
            if (!saw_diagnostics_only) {
                std::cerr << "maintained shortcut did not report diagnostics-only failure\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_belief_to_action_intent_requires_valid_decision_belief_provenance() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            DecisionBelief belief{};
            belief.belief_id = "belief:missing-provenance";
            belief.information_state_layer = "DecisionBelief";
            belief.source_information_state.information_state_layer =
                "AgentObservation";
            belief.source_information_state.source_label =
                "facade_observation_packet";
            belief.source_information_state.maintained_status = "maintained";
            belief.memory_or_estimator_ref = "estimator:belief";
            belief.maintained_status = "maintained";

            ActionIntentPacket intent{};
            intent.source_id = "policy:blue:11";
            intent.action_family = "direct_control";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.has_pilot_action = true;

            InformationTransformationEvidence db_to_ai{};
            db_to_ai.transformation_name =
                std::string(kCanonicalTransformationDecisionBeliefToActionIntent);
            db_to_ai.source_layer = "DecisionBelief";
            db_to_ai.target_layer = "ActionIntentPacket";
            db_to_ai.maintained_status = "maintained";
            db_to_ai.source_observation_versions = {"belief:missing-provenance"};
            db_to_ai.evidence_tokens = {"intent_injection_evidence"};

            const auto result =
                validate_decision_belief_to_action_intent_transformation(
                    belief,
                    intent,
                    db_to_ai);
            if (result.valid) {
                std::cerr << "belief-to-intent accepted invalid belief provenance\n";
                return 1;
            }

            bool saw_provenance_error = false;
            for (const auto& error : result.errors) {
                saw_provenance_error =
                    saw_provenance_error ||
                    error.find("DecisionBelief provenance") != std::string::npos ||
                    error.find("DecisionBelief.source_observation_versions") !=
                        std::string::npos;
            }
            if (!saw_provenance_error) {
                std::cerr << "missing provenance failure was not explained\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp12_diagnostics_only_world_truth_shortcut_remains_explicit_not_maintained() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include "runtime/contracts/information_transform_contracts.h"

        int main() {
            using namespace runtime::information;

            InformationStateSource truth{};
            truth.information_state_layer = "WorldTruth";
            truth.source_label = "world_truth_diagnostics";
            truth.maintained_status = "diagnostics_only";
            truth.source_observation_versions = {"truth:7"};
            truth.diagnostics_reason = "oracle replay";

            ActionIntentPacket intent{};
            intent.source_id = "oracle:7";
            intent.action_family = "direct_control";
            intent.action_interface.kind = "PilotActionAssignmentCompat";
            intent.has_pilot_action = true;

            InformationTransformationEvidence shortcut{};
            shortcut.transformation_name =
                std::string(kDiagnosticsOnlyTransformationWorldTruthToActionIntent);
            shortcut.source_layer = "WorldTruth";
            shortcut.target_layer = "ActionIntentPacket";
            shortcut.maintained_status = "diagnostics_only";
            shortcut.source_observation_versions = {"truth:7"};
            shortcut.evidence_tokens = {"intent_injection_evidence"};
            shortcut.diagnostics_reason = "oracle replay";

            const auto result =
                validate_information_source_to_action_intent_transformation(
                    truth,
                    intent,
                    shortcut);
            if (!result.valid) {
                std::cerr << "diagnostics-only shortcut should stay explicit and valid\n";
                return 1;
            }
            return 0;
        }
        """
    )
    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
