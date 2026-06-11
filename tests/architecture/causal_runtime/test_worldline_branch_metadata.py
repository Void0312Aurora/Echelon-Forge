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
  return compile_cpp_snippet(source, binary_prefix="causal_worldline_branch")


def test_wp15_worldline_branch_metadata_header_declares_required_surface() -> None:
  text = HEADER.read_text(encoding="utf-8")
  constants = CONSTANTS.read_text(encoding="utf-8")

  for symbol in (
    "struct WorldlineBranchMetadata",
    "struct WorldlineBranchSupportResult",
    "validate_worldline_branch_metadata",
    "validate_worldline_branch_metadata_against_branch_point",
    "validate_worldline_branch_metadata_for_snapshot_restore",
    "ordered_worldline_branch_evidence_refs",
    "kWorldlineBranchSupportStateMetadataOnly",
    "kWorldlineBranchSupportStateRestoreUnsupported",
    "kWorldlineBranchSupportStateAdmitted",
    "kWorldlineBranchMutationIntentMetadataOnly",
    "kWorldlineBranchRejectionRawStateMutationForbidden",
    "kWorldlineBranchRejectionMissingEvidenceRefs",
  ):
    assert symbol in text or symbol in constants

  assert "generation_request.py" not in text


def test_wp15_valid_worldline_branch_metadata_fixture_is_bounded_restore_capable() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include <vector>
    #include "runtime/contracts/counterfactual_replay_contracts.h"

    namespace {

    runtime::counterfactual::ReplayEnvelope make_envelope() {
      using namespace runtime::counterfactual;

      ReplayEnvelope envelope{};
      envelope.replay_envelope_id = "replay:baseline:0007";
      envelope.run_id = "run:baseline";
      envelope.episode_id = "episode:7";
      envelope.has_deterministic_seed = true;
      envelope.deterministic_seed = 7;
      envelope.has_source_time = true;
      envelope.source_time_s = 5.5;
      envelope.snapshot_ref.snapshot_version_ref = "global:7";
      envelope.barrier_ref.barrier_id = "window_commit";
      envelope.barrier_ref.barrier_sequence = 3;
      envelope.barrier_ref.barrier_detail = "maintained_facade_export";
      envelope.event_order_ref.event_id = "event:7";
      envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
      envelope.facade_provenance_ref.packet_ref = "obs:7";
      return envelope;
    }

    runtime::counterfactual::BranchPoint make_branch_point(
      const runtime::counterfactual::ReplayEnvelope& envelope
    ) {
      using namespace runtime::counterfactual;

      BranchPoint branch_point{};
      branch_point.branch_point_id = make_branch_point_identity(envelope);
      branch_point.replay_envelope_id = envelope.replay_envelope_id;
      branch_point.snapshot_version_ref = envelope.snapshot_ref.snapshot_version_ref;
      branch_point.barrier_id = envelope.barrier_ref.barrier_id;
      branch_point.event_order_ref = envelope.event_order_ref.event_id;
      branch_point.facade_packet_ref = envelope.facade_provenance_ref.packet_ref;
      return branch_point;
    }

    runtime::counterfactual::WorldlineBranchMetadata make_metadata(
      const runtime::counterfactual::ReplayEnvelope& envelope,
      const runtime::counterfactual::BranchPoint& branch_point
    ) {
      using namespace runtime::counterfactual;

      WorldlineBranchMetadata metadata{};
      metadata.baseline_worldline_id = "worldline:baseline";
      metadata.parent_worldline_id = "worldline:baseline";
      metadata.child_worldline_id = "worldline:child:0001";
      metadata.branch_point_ref = branch_point.branch_point_id;
      metadata.replay_envelope_ref = envelope.replay_envelope_id;
      metadata.branch_reason = "counterfactual_sensor_dropout_probe";
      metadata.intervention_intent = "withhold_sensor_packet";
      metadata.mutation_intent =
        std::string(kWorldlineBranchMutationIntentMetadataOnly);
      metadata.metadata_only = true;
      metadata.source_ref = "source:counterfactual_author";
      metadata.provenance_ref = "prov:obs-derived-branch";
      metadata.evidence_refs = {
        "evidence:facade:obs:7",
        "evidence:branch-point:7",
      };
      metadata.support_state =
        std::string(kWorldlineBranchSupportStateMetadataOnly);
      metadata.snapshot_restore_supported = true;
      metadata.restore_support_boundary =
        std::string(kReplayRestoreSupportBoundaryHostOwnedFacadeStateOnly);
      return metadata;
    }

    } // namespace

    int main() {
      using namespace runtime::counterfactual;

      const ReplayEnvelope envelope = make_envelope();
      const BranchPoint branch_point = make_branch_point(envelope);
      const WorldlineBranchMetadata metadata =
        make_metadata(envelope, branch_point);

      const auto metadata_result =
        validate_worldline_branch_metadata_against_branch_point(
          metadata,
          branch_point,
          envelope
        );
      if (!metadata_result.valid) {
        std::cerr << "valid worldline metadata rejected\n";
        for (const auto& error : metadata_result.errors) {
          std::cerr << error << "\n";
        }
        return 1;
      }

      const std::vector<std::string> refs =
        ordered_worldline_branch_evidence_refs(metadata);
      const std::vector<std::string> expected = {
        "branch_point_ref=branch_point:replay:baseline:0007:global:7:window_commit:event:7",
        "replay_envelope_ref=replay:baseline:0007",
        "source_ref=source:counterfactual_author",
        "provenance_ref=prov:obs-derived-branch",
        "evidence_ref=evidence:facade:obs:7",
        "evidence_ref=evidence:branch-point:7",
      };
      if (refs != expected) {
        std::cerr << "metadata evidence ref ordering drifted\n";
        return 1;
      }

      const auto support =
        validate_worldline_branch_metadata_for_snapshot_restore(
          metadata,
          branch_point,
          envelope
        );
      if (!support.supported ||
        support.support_state != kWorldlineBranchSupportStateAdmitted ||
        !support.rejection_reason.empty()) {
        std::cerr << "bounded restore support drifted for metadata-only branch\n";
        return 1;
      }

      return 0;
    }
    """
  )

  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_worldline_branch_metadata_missing_required_fields_fail_closed() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "runtime/contracts/counterfactual_replay_contracts.h"

    int main() {
      using namespace runtime::counterfactual;

      WorldlineBranchMetadata metadata{};
      metadata.mutation_intent.clear();
      const auto result = validate_worldline_branch_metadata(metadata);
      if (result.valid ||
        result.rejection_reason !=
          kWorldlineBranchRejectionMissingBaselineWorldlineId) {
        std::cerr << "missing baseline worldline id did not fail first\n";
        return 1;
      }

      bool saw_parent = false;
      bool saw_child = false;
      bool saw_branch_point = false;
      bool saw_replay_envelope = false;
      bool saw_branch_reason = false;
      bool saw_intervention_intent = false;
      bool saw_mutation_intent = false;
      bool saw_source = false;
      bool saw_provenance = false;
      bool saw_evidence = false;
      for (const auto& error : result.errors) {
        saw_parent = saw_parent ||
          error.find("parent_worldline_id") != std::string::npos;
        saw_child = saw_child ||
          error.find("child_worldline_id") != std::string::npos;
        saw_branch_point = saw_branch_point ||
          error.find("branch_point_ref") != std::string::npos;
        saw_replay_envelope = saw_replay_envelope ||
          error.find("replay_envelope_ref") != std::string::npos;
        saw_branch_reason = saw_branch_reason ||
          error.find("branch_reason") != std::string::npos;
        saw_intervention_intent = saw_intervention_intent ||
          error.find("intervention_intent") != std::string::npos;
        saw_mutation_intent = saw_mutation_intent ||
          error.find("mutation_intent") != std::string::npos;
        saw_source = saw_source ||
          error.find("source_ref") != std::string::npos;
        saw_provenance = saw_provenance ||
          error.find("provenance_ref") != std::string::npos;
        saw_evidence = saw_evidence ||
          error.find("evidence_refs") != std::string::npos;
      }

      if (!saw_parent || !saw_child || !saw_branch_point ||
        !saw_replay_envelope || !saw_branch_reason ||
        !saw_intervention_intent || !saw_mutation_intent ||
        !saw_source || !saw_provenance || !saw_evidence) {
        std::cerr << "missing-field coverage incomplete\n";
        return 1;
      }

      return 0;
    }
    """
  )

  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_worldline_branch_metadata_rejects_raw_state_mutation_and_invalid_source_labels() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "runtime/contracts/counterfactual_replay_contracts.h"

    namespace {

    runtime::counterfactual::WorldlineBranchMetadata make_metadata() {
      using namespace runtime::counterfactual;

      WorldlineBranchMetadata metadata{};
      metadata.baseline_worldline_id = "worldline:baseline";
      metadata.parent_worldline_id = "worldline:baseline";
      metadata.child_worldline_id = "worldline:child:0002";
      metadata.branch_point_ref = "branch_point:valid";
      metadata.replay_envelope_ref = "replay:valid";
      metadata.branch_reason = "counterfactual_route_probe";
      metadata.intervention_intent = "replace_waypoint_logic";
      metadata.mutation_intent =
        std::string(kWorldlineBranchMutationIntentMetadataOnly);
      metadata.metadata_only = true;
      metadata.source_ref = "source:operator";
      metadata.provenance_ref = "prov:operator-note";
      metadata.evidence_refs = {"evidence:route:1"};
      metadata.support_state =
        std::string(kWorldlineBranchSupportStateMetadataOnly);
      return metadata;
    }

    } // namespace

    int main() {
      using namespace runtime::counterfactual;

      WorldlineBranchMetadata raw_mutation = make_metadata();
      raw_mutation.requests_authoritative_state_mutation = true;
      raw_mutation.mutation_intent =
        std::string(kWorldlineBranchMutationIntentRawAuthoritativeStateMutation);
      const auto mutation_result =
        validate_worldline_branch_metadata(raw_mutation);
      if (mutation_result.valid ||
        mutation_result.rejection_reason !=
          kWorldlineBranchRejectionRawStateMutationForbidden) {
        std::cerr << "raw authoritative state mutation was not rejected\n";
        return 1;
      }

      WorldlineBranchMetadata invalid_source = make_metadata();
      invalid_source.source_information_state.source_label = "invalid_label";
      const auto source_result =
        validate_worldline_branch_metadata(invalid_source);
      if (source_result.valid ||
        source_result.rejection_reason !=
          kWorldlineBranchRejectionInvalidSourceLabel) {
        std::cerr << "invalid source label was not rejected\n";
        return 1;
      }

      WorldlineBranchMetadata invalid_boundary = make_metadata();
      invalid_boundary.snapshot_restore_supported = true;
      invalid_boundary.restore_support_boundary = "resident_state_clone";
      const auto boundary_result =
        validate_worldline_branch_metadata(invalid_boundary);
      if (boundary_result.valid ||
        boundary_result.rejection_reason !=
          kWorldlineBranchRejectionRestoreBoundaryInvalid) {
        std::cerr << "unsupported restore boundary was not rejected\n";
        return 1;
      }

      return 0;
    }
    """
  )

  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout


def test_wp15_worldline_branch_metadata_ancestry_mismatch_fails_closed() -> None:
  source = textwrap.dedent(
    r"""
    #include <iostream>
    #include <string>
    #include "runtime/contracts/counterfactual_replay_contracts.h"

    namespace {

    runtime::counterfactual::ReplayEnvelope make_envelope() {
      using namespace runtime::counterfactual;

      ReplayEnvelope envelope{};
      envelope.replay_envelope_id = "replay:baseline:0011";
      envelope.run_id = "run:branch";
      envelope.episode_id = "episode:11";
      envelope.has_deterministic_seed = true;
      envelope.deterministic_seed = 11;
      envelope.has_source_time = true;
      envelope.source_time_s = 11.0;
      envelope.snapshot_ref.snapshot_version_ref = "global:11";
      envelope.barrier_ref.barrier_id = "window_commit";
      envelope.barrier_ref.barrier_detail = "maintained_facade_export";
      envelope.event_order_ref.event_id = "event:11";
      envelope.event_order_ref.producer_node_id = "p10.observation_export.v1";
      envelope.facade_provenance_ref.packet_ref = "obs:11";
      return envelope;
    }

    runtime::counterfactual::BranchPoint make_branch_point(
      const runtime::counterfactual::ReplayEnvelope& envelope
    ) {
      using namespace runtime::counterfactual;

      BranchPoint branch_point{};
      branch_point.branch_point_id = make_branch_point_identity(envelope);
      branch_point.replay_envelope_id = envelope.replay_envelope_id;
      branch_point.snapshot_version_ref = envelope.snapshot_ref.snapshot_version_ref;
      branch_point.barrier_id = envelope.barrier_ref.barrier_id;
      branch_point.event_order_ref = envelope.event_order_ref.event_id;
      branch_point.facade_packet_ref = envelope.facade_provenance_ref.packet_ref;
      return branch_point;
    }

    runtime::counterfactual::WorldlineBranchMetadata make_metadata(
      const runtime::counterfactual::ReplayEnvelope& envelope,
      const runtime::counterfactual::BranchPoint& branch_point
    ) {
      using namespace runtime::counterfactual;

      WorldlineBranchMetadata metadata{};
      metadata.baseline_worldline_id = "worldline:baseline";
      metadata.parent_worldline_id = "worldline:baseline";
      metadata.child_worldline_id = "worldline:child:0011";
      metadata.branch_point_ref = branch_point.branch_point_id;
      metadata.replay_envelope_ref = envelope.replay_envelope_id;
      metadata.branch_reason = "counterfactual_emcon_branch";
      metadata.intervention_intent = "withhold_radar_emission";
      metadata.source_ref = "source:analyst";
      metadata.provenance_ref = "prov:baseline-evidence";
      metadata.evidence_refs = {"evidence:obs:11"};
      return metadata;
    }

    } // namespace

    int main() {
      using namespace runtime::counterfactual;

      const ReplayEnvelope envelope = make_envelope();
      const BranchPoint branch_point = make_branch_point(envelope);

      WorldlineBranchMetadata bad_branch_ref =
        make_metadata(envelope, branch_point);
      bad_branch_ref.branch_point_ref = "branch_point:drift";
      const auto branch_result =
        validate_worldline_branch_metadata_against_branch_point(
          bad_branch_ref,
          branch_point,
          envelope
        );
      if (branch_result.valid ||
        branch_result.rejection_reason !=
          kWorldlineBranchRejectionBranchPointRefMismatch) {
        std::cerr << "branch point ancestry mismatch did not fail closed\n";
        return 1;
      }

      WorldlineBranchMetadata bad_envelope_ref =
        make_metadata(envelope, branch_point);
      bad_envelope_ref.replay_envelope_ref = "replay:drift";
      const auto envelope_result =
        validate_worldline_branch_metadata_against_branch_point(
          bad_envelope_ref,
          branch_point,
          envelope
        );
      if (envelope_result.valid ||
        envelope_result.rejection_reason !=
          kWorldlineBranchRejectionReplayEnvelopeRefMismatch) {
        std::cerr << "replay envelope ancestry mismatch did not fail closed\n";
        return 1;
      }

      return 0;
    }
    """
  )

  result = _compile_and_run(source)
  assert result.returncode == 0, result.stderr + result.stdout
