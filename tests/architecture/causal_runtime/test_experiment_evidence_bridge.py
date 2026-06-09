from __future__ import annotations

import textwrap

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet

HEADER = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "counterfactual_replay_contracts.h"
)
CONSTANTS = (
    REPO_ROOT
    / "src"
    / "runtime"
    / "contracts"
    / "counterfactual_replay_contract_constants.h"
)


def _compile_and_run(source: str):
    return compile_cpp_snippet(source, binary_prefix="causal_experiment_evidence_bridge")


def test_wp15_experiment_evidence_bridge_header_declares_bridge_surface() -> None:
    text = HEADER.read_text(encoding="utf-8")
    constants = CONSTANTS.read_text(encoding="utf-8")

    for symbol in (
        "struct ScenarioGenerationArtifactMetadata",
        "struct ExperimentProfileObservationRef",
        "struct ExperimentEvidenceBridgeRecord",
        "struct ExperimentEvidenceBridgeValidationResult",
        "validate_scenario_generation_artifact_metadata",
        "validate_experiment_profile_observation_ref",
        "validate_experiment_evidence_bridge_record",
        "make_experiment_evidence_bridge_record",
        "ordered_scenario_generation_request_metadata_evidence_refs",
        "ordered_experiment_profile_observation_evidence_refs",
        "ordered_experiment_bridge_evidence_refs",
        "kExperimentEvidenceBridgeRejectionTruthClaimForbidden",
        "kExperimentEvidenceBridgeRejectionSupportPromotionForbidden",
        "kExperimentEvidenceClaimBoundaryNonTruthClaim",
        "kExperimentEvidencePromotionStateNotPromoted",
    ):
        assert symbol in text or symbol in constants


def test_wp15_valid_experiment_evidence_bridge_links_admission_generated_input_and_profile_observation() -> None:
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
            request.request_id = "cf:req:bridge:0001";
            request.baseline_worldline_id = "worldline:baseline";
            request.intervention_kind =
                std::string(kCounterfactualInterventionKindObservationWithhold);
            request.source = std::string(kCounterfactualSourceExperimentPlan);
            request.authority_ref = "authority:operator:bridge";
            request.provenance_ref = "prov:counterfactual:bridge:0001";
            request.authority_scope.scope =
                std::string(kAgentAuthorityScopePlatformControl);
            request.authority_scope.world_index = 1;
            request.authority_scope.has_world_index = true;
            request.authority_scope.entity_ids = {17};
            request.authority_information_state = make_information_state_source(
                kPolicyInformationStateDecisionBelief,
                kPolicySourceLabelObservationDerivedBelief,
                kPolicyMaintainedStatusMaintained
            );
            request.authority_evidence_refs = {
                "authority_record:operator:bridge",
                "decision_belief:bridge:0001",
            };
            request.backend_profile_ref = "cpu_exact.reference";
            request.fidelity_profile_ref = "exact_evaluation";
            request.capability_refs = {
                "capability_bundle:f16c.block50",
                "resolved_spawn_plan:f16c.block50",
            };
            request.evidence_refs = {
                "evidence:baseline_worldline:17",
                "evidence:counterfactual_request:17",
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
                "worldline:variant:0001";
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
            request.worldline_branch_metadata.source_ref = "source:experiment_plan";
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

        runtime::counterfactual::ScenarioGenerationArtifactMetadata
        make_generated_input(
            const runtime::counterfactual::CounterfactualExperimentRequest& request
        ) {
            using namespace runtime::counterfactual;

            ScenarioGenerationArtifactMetadata artifact{};
            artifact.request.request_id = "scenario-gen:req-bridge-001";
            artifact.request.request_version = "1";
            artifact.request.contract_version =
                std::string(kScenarioGenerationContractVersionWp15RequestV1);
            artifact.request.generation_kind =
                std::string(kScenarioGenerationKindAdversaryPlacement);
            artifact.request.source =
                std::string(kScenarioGenerationSourceCounterfactualBranch);
            artifact.request.generator_version = "generator.v1.2.0";
            artifact.request.has_deterministic_seed = true;
            artifact.request.deterministic_seed = 17;
            artifact.request.baseline_scenario_ref = "scenario:baseline:17";
            artifact.request.replay_envelope_ref =
                request.replay_envelope.replay_envelope_id;
            artifact.request.branch_point_ref = request.branch_point.branch_point_id;
            artifact.request.capability_refs = request.capability_refs;
            artifact.request.evidence_refs = {
                {
                    .ref_id = artifact.request.baseline_scenario_ref,
                    .evidence_kind =
                        std::string(kScenarioGenerationEvidenceKindBaselineScenario),
                    .provenance_label = "baseline",
                },
                {
                    .ref_id = request.replay_envelope.replay_envelope_id,
                    .evidence_kind =
                        std::string(kScenarioGenerationEvidenceKindReplayEnvelope),
                    .provenance_label = "replay",
                },
                {
                    .ref_id = request.branch_point.branch_point_id,
                    .evidence_kind =
                        std::string(kScenarioGenerationEvidenceKindBranchPoint),
                    .provenance_label = "branch",
                },
            };
            return artifact;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            const CounterfactualExperimentRequest request = make_request();
            const CounterfactualAdmissionResult admission =
                admit_counterfactual_experiment_request(request);
            if (!admission.admitted) {
                std::cerr << "counterfactual request should admit for bridge test\n";
                return 1;
            }

            const ScenarioGenerationArtifactMetadata generated_input =
                make_generated_input(request);

            ExperimentProfileObservationRef observation{};
            observation.observation_ref = "profile_obs:bridge:0001";
            observation.profile_ref = "profile:capability:f16";
            observation.status =
                std::string(kExperimentProfileObservationStatusObserved);
            observation.claim_scope =
                std::string(kExperimentProfileClaimScopeComparative);
            observation.evidence_refs = {
                "learning_evidence:bridge:0001",
                "benchmark_log:bridge:0001",
            };

            const ExperimentEvidenceBridgeRecord record =
                make_experiment_evidence_bridge_record(
                    admission,
                    request.replay_envelope,
                    generated_input,
                    "experiment_run:bridge:0001",
                    "comparison:baseline_vs_variant:0001",
                    {observation},
                    {
                        "evidence:experiment_plan:0001",
                        "evidence:comparison_sheet:0001",
                    }
                );

            const auto validation = validate_experiment_evidence_bridge_record(
                record,
                admission,
                request.replay_envelope,
                generated_input
            );
            if (!validation.valid || validation.fail_closed) {
                std::cerr << "valid bridge record rejected\n";
                for (const auto& error : validation.errors) {
                    std::cerr << error << "\n";
                }
                return 1;
            }

            const std::vector<std::string> expected_record_refs = {
                "experiment_run_id=experiment_run:bridge:0001",
                "comparison_id=comparison:baseline_vs_variant:0001",
                "replay_run_id=run:alpha",
                "baseline_worldline_id=worldline:baseline",
                "variant_worldline_id=worldline:variant:0001",
                "counterfactual_request_ref=cf:req:bridge:0001",
                "counterfactual_admission_ref=cf:req:bridge:0001",
                "replay_envelope_ref=replay:baseline:17",
                "branch_point_ref=branch_point:replay:baseline:17:global:17:window_commit:event:17",
                "generated_input_ref=scenario-gen:req-bridge-001",
                "backend_profile_ref=cpu_exact.reference",
                "fidelity_profile_ref=exact_evaluation",
                "claim_boundary=non_truth_claim_observation_only",
                "promotion_state=not_promoted",
                "capability_ref=capability_bundle:f16c.block50",
                "capability_ref=resolved_spawn_plan:f16c.block50",
                "profile_observation_ref=profile_obs:bridge:0001",
                "evidence_ref=evidence:experiment_plan:0001",
                "evidence_ref=evidence:comparison_sheet:0001",
            };
            if (ordered_experiment_bridge_evidence_refs(record) !=
                expected_record_refs) {
                std::cerr << "experiment bridge evidence ref ordering drifted\n";
                return 1;
            }

            const std::vector<std::string> expected_generated_refs = {
                "generated_input_request_id=scenario-gen:req-bridge-001",
                "generated_input_generation_kind=adversary_placement",
                "generated_input_source=counterfactual_branch",
                "generated_input_generator_version=generator.v1.2.0",
                "generated_input_baseline_scenario_ref=scenario:baseline:17",
                "generated_input_replay_envelope_ref=replay:baseline:17",
                "generated_input_branch_point_ref=branch_point:replay:baseline:17:global:17:window_commit:event:17",
                "generated_input_capability_ref=capability_bundle:f16c.block50",
                "generated_input_capability_ref=resolved_spawn_plan:f16c.block50",
                "generated_input_evidence_ref=baseline_scenario:scenario:baseline:17:baseline",
                "generated_input_evidence_ref=replay_envelope:replay:baseline:17:replay",
                "generated_input_evidence_ref=branch_point:branch_point:replay:baseline:17:global:17:window_commit:event:17:branch",
            };
            if (ordered_scenario_generation_request_metadata_evidence_refs(generated_input) !=
                expected_generated_refs) {
                std::cerr << "generated input evidence ordering drifted\n";
                return 1;
            }

            const std::vector<std::string> expected_observation_refs = {
                "profile_observation_ref=profile_obs:bridge:0001",
                "profile_ref=profile:capability:f16",
                "profile_status=observed",
                "profile_claim_scope=comparative",
                "profile_evidence_ref=learning_evidence:bridge:0001",
                "profile_evidence_ref=benchmark_log:bridge:0001",
            };
            if (ordered_experiment_profile_observation_evidence_refs(observation) !=
                expected_observation_refs) {
                std::cerr << "profile observation evidence ordering drifted\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_experiment_evidence_bridge_missing_required_fields_fail_closed() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            CounterfactualAdmissionResult admission{};
            ScenarioGenerationArtifactMetadata generated_input{};
            ExperimentEvidenceBridgeRecord record{};

            ExperimentProfileObservationRef observation{};
            observation.observation_ref = "profile_obs:missing";
            observation.profile_ref = "profile:missing";
            observation.status =
                std::string(kExperimentProfileObservationStatusObserved);
            observation.claim_scope =
                std::string(kExperimentProfileClaimScopeDescriptive);
            observation.evidence_refs = {"benchmark_log:missing"};

            record.profile_observation_refs = {observation};

            ReplayEnvelope envelope{};
            const auto result = validate_experiment_evidence_bridge_record(
                record,
                admission,
                envelope,
                generated_input
            );
            if (result.valid ||
                result.rejection_reason !=
                    kExperimentEvidenceBridgeRejectionMissingExperimentRunId ||
                !result.fail_closed) {
                std::cerr << "missing experiment_run_id did not fail first\n";
                return 1;
            }

            bool saw_comparison = false;
            bool saw_baseline = false;
            bool saw_variant = false;
            bool saw_request_ref = false;
            bool saw_admission_ref = false;
            bool saw_generated_input = false;
            bool saw_backend = false;
            bool saw_fidelity = false;
            bool saw_capability = false;
            bool saw_evidence = false;
            for (const auto& error : result.errors) {
                saw_comparison = saw_comparison ||
                    error.find("comparison_id") != std::string::npos;
                saw_baseline = saw_baseline ||
                    error.find("baseline_worldline_id") != std::string::npos;
                saw_variant = saw_variant ||
                    error.find("variant_worldline_id") != std::string::npos;
                saw_request_ref = saw_request_ref ||
                    error.find("counterfactual_request_ref") != std::string::npos;
                saw_admission_ref = saw_admission_ref ||
                    error.find("counterfactual_admission_ref") != std::string::npos;
                saw_generated_input = saw_generated_input ||
                    error.find("generated_input_ref") != std::string::npos;
                saw_backend = saw_backend ||
                    error.find("backend_profile_ref") != std::string::npos;
                saw_fidelity = saw_fidelity ||
                    error.find("fidelity_profile_ref") != std::string::npos;
                saw_capability = saw_capability ||
                    error.find("capability_refs") != std::string::npos;
                saw_evidence = saw_evidence ||
                    error.find("evidence_refs") != std::string::npos;
            }

            if (!saw_comparison || !saw_baseline || !saw_variant ||
                !saw_request_ref || !saw_admission_ref || !saw_generated_input ||
                !saw_backend || !saw_fidelity || !saw_capability || !saw_evidence) {
                std::cerr << "missing-field coverage incomplete\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_experiment_evidence_bridge_rejects_generated_input_mismatch_and_mutation_boundary() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        namespace {

        runtime::counterfactual::CounterfactualAdmissionResult make_admission() {
            using namespace runtime::counterfactual;

            CounterfactualAdmissionResult result{};
            result.admitted = true;
            result.request_id = "cf:req:mismatch";
            result.baseline_worldline_id = "worldline:baseline";
            result.child_worldline_id = "worldline:variant";
            result.replay_envelope_id = "replay:baseline:22";
            result.branch_point_id =
                "branch_point:replay:baseline:22:global:22:window_commit:event:22";
            result.backend_profile_ref = "cpu_exact.reference";
            result.fidelity_profile_ref = "exact_evaluation";
            result.capability_refs = {"capability_bundle:test"};
            result.admission_state =
                std::string(kCounterfactualAdmissionStateAdmitted);
            result.worldline_support_state =
                std::string(kWorldlineBranchSupportStateMetadataOnly);
            return result;
        }

        runtime::counterfactual::ReplayEnvelope make_envelope() {
            using namespace runtime::counterfactual;

            ReplayEnvelope envelope{};
            envelope.replay_envelope_id = "replay:baseline:22";
            envelope.run_id = "run:mismatch";
            envelope.episode_id = "episode:22";
            envelope.has_deterministic_seed = true;
            envelope.deterministic_seed = 22;
            envelope.has_source_time = true;
            envelope.source_time_s = 2.2;
            envelope.snapshot_ref.snapshot_version_ref = "global:22";
            envelope.barrier_ref.barrier_id = "window_commit";
            envelope.barrier_ref.barrier_detail = "maintained_facade_export";
            envelope.event_order_ref.event_id = "event:22";
            envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
            envelope.facade_provenance_ref.packet_ref = "obs:22";
            return envelope;
        }

        runtime::counterfactual::ScenarioGenerationArtifactMetadata
        make_generated_input() {
            using namespace runtime::counterfactual;

            ScenarioGenerationArtifactMetadata artifact{};
            artifact.authoritative_state_mutation_allowed = true;
            artifact.request.request_id = "scenario-gen:req:mismatch";
            artifact.request.request_version = "1";
            artifact.request.contract_version =
                std::string(kScenarioGenerationContractVersionWp15RequestV1);
            artifact.request.generation_kind =
                std::string(kScenarioGenerationKindScenarioVariation);
            artifact.request.source =
                std::string(kScenarioGenerationSourceCounterfactualBranch);
            artifact.request.generator_version = "generator.v1.2.0";
            artifact.request.has_deterministic_seed = true;
            artifact.request.deterministic_seed = 22;
            artifact.request.baseline_scenario_ref = "scenario:baseline:22";
            artifact.request.replay_envelope_ref = "replay:drift";
            artifact.request.branch_point_ref = "branch:drift";
            artifact.request.capability_refs = {"capability_bundle:test"};
            artifact.request.evidence_refs = {{
                .ref_id = "scenario:baseline:22",
                .evidence_kind =
                    std::string(kScenarioGenerationEvidenceKindBaselineScenario),
                .provenance_label = "baseline",
            }};
            return artifact;
        }

        }  // namespace

        int main() {
            using namespace runtime::counterfactual;

            const CounterfactualAdmissionResult admission = make_admission();
            const ReplayEnvelope envelope = make_envelope();
            const ScenarioGenerationArtifactMetadata generated_input =
                make_generated_input();

            ExperimentProfileObservationRef observation{};
            observation.observation_ref = "profile_obs:mismatch";
            observation.profile_ref = "profile:mismatch";
            observation.status =
                std::string(kExperimentProfileObservationStatusObserved);
            observation.claim_scope =
                std::string(kExperimentProfileClaimScopeDescriptive);
            observation.evidence_refs = {"benchmark_log:mismatch"};

            ExperimentEvidenceBridgeRecord record{};
            record.experiment_run_id = "experiment_run:mismatch";
            record.comparison_id = "comparison:mismatch";
            record.replay_run_id = envelope.run_id;
            record.baseline_worldline_id = admission.baseline_worldline_id;
            record.variant_worldline_id = admission.child_worldline_id;
            record.counterfactual_request_ref = admission.request_id;
            record.counterfactual_admission_ref = admission.request_id;
            record.replay_envelope_ref = admission.replay_envelope_id;
            record.branch_point_ref = admission.branch_point_id;
            record.generated_input_ref = generated_input.request.request_id;
            record.backend_profile_ref = admission.backend_profile_ref;
            record.fidelity_profile_ref = admission.fidelity_profile_ref;
            record.capability_refs = admission.capability_refs;
            record.profile_observation_refs = {observation};
            record.evidence_refs = {"evidence:mismatch"};

            const auto result = validate_experiment_evidence_bridge_record(
                record,
                admission,
                envelope,
                generated_input
            );
            if (result.valid ||
                result.rejection_reason !=
                    kExperimentEvidenceBridgeRejectionGeneratedInputMutationForbidden ||
                !result.fail_closed) {
                std::cerr << "generated input mutation boundary did not fail first\n";
                return 1;
            }

            bool saw_replay_mismatch = false;
            bool saw_branch_mismatch = false;
            for (const auto& error : result.errors) {
                saw_replay_mismatch = saw_replay_mismatch ||
                    error.find("generated input replay_envelope_ref") != std::string::npos;
                saw_branch_mismatch = saw_branch_mismatch ||
                    error.find("generated input branch_point_ref") != std::string::npos;
            }
            if (!saw_replay_mismatch || !saw_branch_mismatch) {
                std::cerr << "generated input mismatch evidence incomplete\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_experiment_evidence_bridge_rejects_truth_claim_and_support_promotion() -> None:
    source = textwrap.dedent(
        r"""
        #include <iostream>
        #include <string>
        #include "runtime/contracts/counterfactual_replay_contracts.h"

        int main() {
            using namespace runtime::counterfactual;

            ExperimentProfileObservationRef truthy{};
            truthy.observation_ref = "profile_obs:truthy";
            truthy.profile_ref = "profile:truthy";
            truthy.status = std::string(kExperimentProfileObservationStatusObserved);
            truthy.claim_scope =
                std::string(kExperimentProfileClaimScopeDescriptive);
            truthy.truth_claim = true;
            truthy.evidence_refs = {"benchmark_log:truthy"};

            const auto truthy_result =
                validate_experiment_profile_observation_ref(truthy);
            if (truthy_result.valid ||
                truthy_result.rejection_reason !=
                    kExperimentEvidenceBridgeRejectionProfileObservationTruthClaimForbidden) {
                std::cerr << "truth-claim observation did not fail closed\n";
                return 1;
            }

            ExperimentProfileObservationRef promoted = truthy;
            promoted.truth_claim = false;
            promoted.promoted_to_support = true;
            const auto promoted_result =
                validate_experiment_profile_observation_ref(promoted);
            if (promoted_result.valid ||
                promoted_result.rejection_reason !=
                    kExperimentEvidenceBridgeRejectionProfileObservationSupportPromotionForbidden) {
                std::cerr << "support-promotion observation did not fail closed\n";
                return 1;
            }

            ExperimentEvidenceBridgeRecord record{};
            record.experiment_run_id = "experiment_run:truthy";
            record.comparison_id = "comparison:truthy";
            record.replay_run_id = "run:truthy";
            record.baseline_worldline_id = "worldline:baseline";
            record.variant_worldline_id = "worldline:variant";
            record.counterfactual_request_ref = "cf:req:truthy";
            record.counterfactual_admission_ref = "cf:req:truthy";
            record.replay_envelope_ref = "replay:truthy";
            record.branch_point_ref = "branch:truthy";
            record.generated_input_ref = "scenario-gen:req:truthy";
            record.backend_profile_ref = "cpu_exact.reference";
            record.fidelity_profile_ref = "exact_evaluation";
            record.capability_refs = {"capability_bundle:test"};
            record.profile_observation_refs = {truthy};
            record.evidence_refs = {"evidence:truthy"};
            record.truth_claim = true;

            CounterfactualAdmissionResult admission{};
            ReplayEnvelope envelope{};
            ScenarioGenerationArtifactMetadata generated_input{};
            const auto record_result = validate_experiment_evidence_bridge_record(
                record,
                admission,
                envelope,
                generated_input
            );
            if (record_result.valid ||
                record_result.rejection_reason !=
                    kExperimentEvidenceBridgeRejectionTruthClaimForbidden ||
                !record_result.fail_closed) {
                std::cerr << "truth-claim record did not fail closed\n";
                return 1;
            }

            return 0;
        }
        """
    )

    result = _compile_and_run(source)
    assert result.returncode == 0, result.stderr + result.stdout
