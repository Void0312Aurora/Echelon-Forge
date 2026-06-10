from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DTO_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "runtime_dto_contracts.h"
FACADE_TYPES = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _struct_body(header: str, struct_name: str) -> str:
    pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
    match = re.search(pattern, header, flags=re.DOTALL)
    assert match is not None, f"{struct_name} missing from {DTO_HEADER}"
    return match.group("body")


def test_runtime_dto_contract_header_exists_at_stable_runtime_contract_path() -> None:
    assert DTO_HEADER.is_file()


def test_runtime_dto_contract_header_does_not_include_core_or_engine_layers() -> None:
    include_lines = re.findall(
        r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]",
        _text(DTO_HEADER),
        flags=re.MULTILINE,
    )
    forbidden = [
        include_path
        for include_path in include_lines
        if "core/" in include_path or "engine/" in include_path
    ]
    assert forbidden == []


def test_reward_report_and_termination_spec_expose_required_typed_fields() -> None:
    header = _text(DTO_HEADER)
    reward_report = _struct_body(header, "RewardReport")
    termination_spec = _struct_body(header, "TerminationSpec")

    for field in (
        "fact_terms",
        "shaping_terms",
        "fact_snapshot_version",
        "term_owner",
    ):
        assert field in reward_report

    for field in ("reason", "reason_source", "snapshot_version"):
        assert field in termination_spec


def test_observation_view_spec_exposes_versioned_checkpoint_compatibility_surface() -> None:
    header = _text(DTO_HEADER)
    view_spec = _struct_body(header, "ObservationViewSpec")
    compatibility_report = _struct_body(header, "ObservationViewCompatibilityReport")

    for field in (
        "schema_version",
        "required_fields",
        "optional_fields",
        "reject_major_mismatch",
        "allow_minor_version_drift",
    ):
        assert field in view_spec

    for field in (
        "compatible",
        "major_compatible",
        "required_fields_satisfied",
        "optional_field_drift_allowed",
        "missing_required_fields",
    ):
        assert field in compatibility_report

    header_text = _text(DTO_HEADER)
    assert "evaluate_observation_view_checkpoint_compatibility" in header_text
    assert "parse_observation_schema_version" in header_text


def test_observation_batch_packet_and_step_result_surface_promote_batch1_dtos() -> None:
    header = _text(FACADE_TYPES)
    packet = _struct_body(header, "ObservationBatchPacket")
    step_result = _struct_body(header, "ExecutionBatchStepResult")

    for field in ("snapshot_version", "barrier_id", "source_time_s"):
        assert field in packet

    for field in ("termination_specs", "reward_reports"):
        assert field in step_result


def test_device_resident_output_descriptor_stays_additive_export_only_surface() -> None:
    header = _text(FACADE_TYPES)
    descriptor = _struct_body(header, "DeviceResidentOutputDescriptor")
    capabilities = _struct_body(header, "RuntimeCapabilities")

    for required in (
        "output_shape",
        "dtype",
        "element_count",
        "source_snapshot",
        "sync_or_export_barrier",
        "host_visible_availability",
        "diagnostics_label",
        "consumer_constraints",
    ):
        assert required in descriptor

    assert "DeviceResidentOutputDescriptor" not in capabilities
    for forbidden in (
        "output_shape",
        "dtype",
        "element_count",
        "source_snapshot",
        "sync_or_export_barrier",
        "host_visible_availability",
        "diagnostics_label",
        "consumer_constraints",
    ):
        assert forbidden not in capabilities, (
            "RuntimeCapabilities must stay a support projection, not a "
            f"device-output transport schema; found {forbidden!r}"
        )


def test_host_visible_packets_do_not_inline_device_resident_descriptor_fields() -> None:
    header = _text(FACADE_TYPES)
    observation_packet = _struct_body(header, "ObservationBatchPacket")
    engagement_packet = _struct_body(header, "EngagementEventPacket")

    for required in (
        "snapshot_version",
        "barrier_id",
        "InformationStateSource provenance",
    ):
        assert required in observation_packet

    for required in (
        "snapshot_version",
        "barrier_id",
        "barrier_sequence",
        "InformationStateSource packet_provenance",
        "InformationStateSource diagnostics_provenance",
    ):
        assert required in engagement_packet

    for forbidden in (
        "device_ptr",
        "device_pointer",
        "device_buffer",
        "device_address",
        "output_shape",
        "dtype",
        "element_count",
        "host_visible_availability",
        "consumer_constraints",
    ):
        assert forbidden not in observation_packet, (
            "ObservationBatchPacket must remain a host-visible export envelope; "
            f"found device-resident descriptor token {forbidden!r}"
        )
        assert forbidden not in engagement_packet, (
            "EngagementEventPacket must remain a host-visible export envelope; "
            f"found device-resident descriptor token {forbidden!r}"
        )
