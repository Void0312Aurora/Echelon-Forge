#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


MANIFEST_SCHEMA_VERSION = "mlf10.calibration_evidence_manifest.v1"
RECORD_SCHEMA_VERSION = "mlf10.calibration_evidence.v1"
REPORT_SCHEMA_VERSION = "mlf10.calibration_admission_report.v1"

CLASSIFICATIONS = (
    "engineering_proxy",
    "retained_non_authoritative",
    "calibration_candidate",
    "admitted",
    "rejected",
    "blocked",
)
AUTHORITY_FIELDS = (
    "effect_scale_authority",
    "component_failure_probability_authority",
    "pk_authority",
    "deterministic_fuze_authority",
    "reward_authority",
    "entity_deletion_authority",
)
ELIGIBLE_AUTHORITY_FIELDS = {
    "effect_scale_authority",
    "component_failure_probability_authority",
}
FORBIDDEN_AUTHORITY_FIELDS = set(AUTHORITY_FIELDS) - ELIGIBLE_AUTHORITY_FIELDS
AUTHORITY_ELIGIBLE_SOURCE_KINDS = {
    "external_calibration_dataset",
    "validated_physics_surrogate",
}
REJECTED_SOURCE_KINDS = {
    "rejected",
    "restricted",
    "leaked",
    "unstable",
    "untraceable",
    "rights_unclear",
    "scope_mismatched",
}
REQUIRED_SCOPE_FIELDS = (
    "target_type",
    "weapon_family",
    "mechanism_family",
    "aspect_bucket",
    "closure_bucket",
    "miss_distance_bucket",
)
REQUIRED_NON_CLAIMS = (
    "real_world_pk",
    "deterministic_fuze_reliability",
    "reward_authority",
    "entity_deletion_authority",
    "out_of_scope_weapon_truth",
    "out_of_scope_target_truth",
)
INVALID_SCOPE_VALUES = {"", "*", "all", "any", "global", "all_platforms", "all_weapons"}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [_string(item) for item in value if _string(item)]


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _requested_authorities(record: Mapping[str, Any]) -> list[str]:
    requests = _mapping(record.get("authority_requests"))
    return [field for field in AUTHORITY_FIELDS if bool(requests.get(field, False))]


def _scope_blockers(scope: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for field in REQUIRED_SCOPE_FIELDS:
        value = _string(scope.get(field)).lower()
        if value in INVALID_SCOPE_VALUES:
            blockers.append(f"scope_{field}_missing_or_broad")
    return blockers


def _population_blockers(population: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not _string(population.get("identity")):
        blockers.append("population_identity_missing")
    if not _string(population.get("denominator_name")):
        blockers.append("population_denominator_missing")
    if _positive_int(population.get("sample_count")) <= 0:
        blockers.append("population_sample_count_invalid")
    if not _string(population.get("filters")):
        blockers.append("population_filters_missing")
    if not _string(population.get("independence_assumption")):
        blockers.append("population_independence_assumption_missing")
    return blockers


def _uncertainty_blockers(uncertainty: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not _string(uncertainty.get("method")):
        blockers.append("uncertainty_method_missing")
    if not _string(uncertainty.get("coverage")):
        blockers.append("uncertainty_coverage_missing")
    if _string_list(uncertainty.get("residuals")):
        blockers.append("uncertainty_residuals_open")
    return blockers


def _common_authority_blockers(
    record: Mapping[str, Any],
    *,
    manifest_blockers: Sequence[str],
) -> list[str]:
    blockers = list(manifest_blockers)
    if _string(record.get("schema_version")) != RECORD_SCHEMA_VERSION:
        blockers.append("record_schema_version_invalid")
    if _string(record.get("source_kind")) not in AUTHORITY_ELIGIBLE_SOURCE_KINDS:
        blockers.append("source_kind_not_authority_eligible")
    if not _string(record.get("source_ref")):
        blockers.append("source_ref_missing")
    if not _string(record.get("provenance")):
        blockers.append("provenance_missing")
    if _string(record.get("rights_status")) != "release_grade_admitted":
        blockers.append("rights_not_release_grade_admitted")
    if _string(record.get("source_gate_status")) != "passed":
        blockers.append("source_gate_not_passed")
    if _string(record.get("validation_status")) != "passed":
        blockers.append("validation_not_passed")

    blockers.extend(_scope_blockers(_mapping(record.get("scope"))))
    blockers.extend(_population_blockers(_mapping(record.get("population"))))
    blockers.extend(_uncertainty_blockers(_mapping(record.get("uncertainty"))))

    review = _mapping(record.get("independent_review"))
    if _string(review.get("status")) != "passed":
        blockers.append("independent_review_not_passed")
    if not _string(review.get("reviewer_ref")):
        blockers.append("independent_reviewer_ref_missing")

    if _string_list(record.get("residuals")):
        blockers.append("blocking_residuals_open")

    non_claims = set(_string_list(record.get("non_claims")))
    for claim in REQUIRED_NON_CLAIMS:
        if claim not in non_claims:
            blockers.append(f"required_non_claim_missing:{claim}")
    return sorted(set(blockers))


def _is_explicitly_rejected(record: Mapping[str, Any]) -> bool:
    return (
        _string(record.get("evidence_class")) == "rejected"
        or _string(record.get("source_kind")) in REJECTED_SOURCE_KINDS
        or _string(record.get("rights_status")) == "rejected"
        or _string(record.get("source_gate_status")) == "rejected"
        or _string(record.get("validation_status")) == "rejected"
    )


def audit_evidence_record(
    record: Mapping[str, Any],
    *,
    manifest_blockers: Sequence[str] = (),
) -> dict[str, Any]:
    normalized = dict(record)
    evidence_id = _string(normalized.get("evidence_id")) or "missing_evidence_id"
    requested = _requested_authorities(normalized)
    residuals = _string_list(normalized.get("residuals"))
    authority_decisions: dict[str, dict[str, Any]] = {}

    if _is_explicitly_rejected(normalized):
        for field in AUTHORITY_FIELDS:
            authority_decisions[field] = {
                "requested": field in requested,
                "decision": "rejected" if field in requested else "not_requested",
                "reasons": ["evidence_explicitly_rejected"] if field in requested else [],
            }
        return {
            "evidence_id": evidence_id,
            "classification": "rejected",
            "gate_status": "rejected",
            "blocking_reasons": ["evidence_explicitly_rejected"],
            "residuals": residuals,
            "scope": _mapping(normalized.get("scope")),
            "authority_decisions": authority_decisions,
        }

    common_blockers = _common_authority_blockers(
        normalized,
        manifest_blockers=manifest_blockers,
    )
    admitted_fields: list[str] = []
    all_blockers: list[str] = []
    for field in AUTHORITY_FIELDS:
        is_requested = field in requested
        reasons: list[str] = []
        decision = "not_requested"
        if is_requested:
            if field in FORBIDDEN_AUTHORITY_FIELDS:
                reasons.append(f"authority_forbidden_in_v1:{field}")
            else:
                reasons.extend(common_blockers)
                if (
                    field == "component_failure_probability_authority"
                    and "component" not in _string(normalized.get("provenance")).lower()
                    and "fragility" not in _string(normalized.get("provenance")).lower()
                ):
                    reasons.append("component_fragility_provenance_missing")
            reasons = sorted(set(reasons))
            if reasons:
                decision = "blocked"
                all_blockers.extend(reasons)
            else:
                decision = "admitted"
                admitted_fields.append(field)
        authority_decisions[field] = {
            "requested": is_requested,
            "decision": decision,
            "reasons": reasons,
        }

    if requested:
        if all_blockers:
            classification = "blocked"
            gate_status = "fail_closed"
        else:
            classification = "admitted"
            gate_status = "passed"
    else:
        input_class = _string(normalized.get("evidence_class"))
        if input_class == "engineering_proxy":
            classification = "engineering_proxy"
        elif input_class == "calibration_candidate":
            classification = "calibration_candidate"
        elif input_class == "blocked":
            classification = "blocked"
        else:
            classification = "retained_non_authoritative"
        gate_status = "not_requested" if classification != "blocked" else "fail_closed"
        if classification == "blocked":
            all_blockers.extend(residuals or ["evidence_marked_blocked"])

    return {
        "evidence_id": evidence_id,
        "classification": classification,
        "gate_status": gate_status,
        "blocking_reasons": sorted(set(all_blockers)),
        "residuals": residuals,
        "scope": _mapping(normalized.get("scope")),
        "admitted_authority_fields": admitted_fields,
        "authority_decisions": authority_decisions,
    }


def audit_manifest(
    manifest: Mapping[str, Any],
    *,
    manifest_ref: str = "",
    report_surface: str = "standalone_retained_diagnostics_artifact",
) -> dict[str, Any]:
    manifest_blockers: list[str] = []
    if _string(manifest.get("schema_version")) != MANIFEST_SCHEMA_VERSION:
        manifest_blockers.append("manifest_schema_version_invalid")

    manifest_non_claims = set(_string_list(manifest.get("non_claims")))
    for claim in REQUIRED_NON_CLAIMS:
        if claim not in manifest_non_claims:
            manifest_blockers.append(f"manifest_non_claim_missing:{claim}")

    raw_records = manifest.get("evidence_records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        raise ValueError("manifest evidence_records must be a list")
    records = [dict(item) for item in raw_records if isinstance(item, Mapping)]
    evidence_ids = [_string(record.get("evidence_id")) for record in records]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("manifest evidence_id values must be unique")

    decisions = [
        audit_evidence_record(record, manifest_blockers=manifest_blockers)
        for record in sorted(records, key=lambda item: _string(item.get("evidence_id")))
    ]
    counts = Counter(decision["classification"] for decision in decisions)
    admitted_authorities = [
        {
            "evidence_id": decision["evidence_id"],
            "authority_field": field,
            "scope": decision["scope"],
        }
        for decision in decisions
        for field in decision.get("admitted_authority_fields", [])
    ]
    decision_counts = {name: int(counts.get(name, 0)) for name in CLASSIFICATIONS}

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "calibration_admission_audit_complete",
        "source_manifest_schema_version": _string(manifest.get("schema_version")),
        "source_manifest_ref": _string(manifest_ref),
        "report_surface": _string(report_surface),
        "record_count": len(decisions),
        "decision_counts": decision_counts,
        "manifest_blocking_reasons": sorted(set(manifest_blockers)),
        "decisions": decisions,
        "admitted_authorities": admitted_authorities,
        "non_claims": list(REQUIRED_NON_CLAIMS),
        "authority_boundary": {
            "admitted_record_count": decision_counts["admitted"],
            "real_world_pk": False,
            "deterministic_fuze_reliability": False,
            "reward_authority": False,
            "entity_deletion_authority": False,
        },
    }


def _load_manifest(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("manifest JSON root must be an object")
    return dict(payload)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit MLF-10 calibration evidence with fail-closed defaults.",
    )
    parser.add_argument("--manifest_json", required=True)
    parser.add_argument("--json_out", default="")
    parser.add_argument(
        "--report_surface",
        default="standalone_retained_diagnostics_artifact",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = audit_manifest(
        _load_manifest(args.manifest_json),
        manifest_ref=str(args.manifest_json).replace("\\", "/"),
        report_surface=str(args.report_surface),
    )
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.json_out:
        output_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
