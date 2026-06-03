#!/usr/bin/env python3
"""Close out RES-004 only for Stage B warhead-family scope.

This gate consumes the frozen warhead scope/sensitivity surface plus retained
provenance and mechanism-source gates. It can close only the Stage B
effect-scale AIM-120C-class blast-fragmentation family-scope slice. It keeps
missile-specific AIM-120C warhead truth, toy numeric authority, fuzing, Pk,
stock/runtime, and component probability authority forbidden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
GATE_SCHEMA_VERSION = "a2.res004_warhead_scope_closeout_gate.v1"
MANIFEST_SCHEMA_VERSION = "a2.res004_warhead_scope_closeout_manifest.v1"
GENERATED_ON = "2026-05-31"
WORKER_ID = "A2-RES004-WARHEAD-SCOPE-CLOSEOUT"

PACKAGE_DIR = (
    REPO_ROOT
    / "docs"
    / "task"
    / "air_combat"
    / "archive"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
DEFAULT_OUTPUT_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "res004_warhead_scope_closeout_20260531"
)
DEFAULT_DOC_OUTPUT = (
    PACKAGE_DIR / "validation_res004_warhead_scope_closeout_gate_20260531.zh.md"
)

EXPECTED_ASSUMPTION_IDS = [
    "WAR-001",
    "WAR-002",
    "WAR-003",
    "WAR-004",
    "WAR-005",
    "WAR-006",
    "WAR-007",
]
EXPECTED_CONSUMED_ASSUMPTION_IDS = ["WAR-001", "WAR-002", "WAR-005"]
EXPECTED_NON_RELEASE_ASSUMPTION_IDS = ["WAR-003", "WAR-004", "WAR-006", "WAR-007"]
EXPECTED_SOURCE_IDS = [
    "AIM120-WF-002",
    "AIM120-WF-006",
    "AIM120-WF-007",
    "PHYS-BF-001",
    "PHYS-BF-002",
    "PHYS-BF-006",
]
EXPECTED_RES004_PIN_IDS = [
    "PIN-AIM120-001",
    "PIN-AIM120-002",
    "PIN-AIM120-TPC-001",
    "PIN-AIM120-TPC-REJ",
]


def _a2_root(repo_root: Path) -> Path:
    return repo_root / "docs" / "task" / "air_combat" / "archive" / "a2_high_fidelity_damage_model"


def _evidence_refs(
    *, package_dir: Path, repo_root: Path
) -> dict[str, tuple[Path, bool, str]]:
    retained = package_dir / "retained_artifacts"
    return {
        "residual_register": (
            package_dir / "residual_register.zh.md",
            True,
            "canonical_residual_status",
        ),
        "warhead_scope_and_sensitivity": (
            package_dir / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md",
            True,
            "res004_stage_b_scope_surface",
        ),
        "artifact_pin_manifest": (
            package_dir / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md",
            True,
            "res004_source_pin_boundary",
        ),
        "warhead_source_ledger": (
            _a2_root(repo_root)
            / "data_collection"
            / "aim120c_warhead_fuze"
            / "source_ledger.zh.md",
            True,
            "res004_public_source_ledger",
        ),
        "geometry_warhead_row_provenance_gate": (
            retained
            / "geometry_warhead_row_provenance_20260531"
            / "geometry_warhead_row_provenance_gate.json",
            True,
            "res004_row_provenance_interlock",
        ),
        "mechanism_source_closeout_gate": (
            retained
            / "mechanism_source_closeout_20260531"
            / "mechanism_source_closeout_gate.json",
            True,
            "res004_mechanism_source_interlock",
        ),
    }


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _doc_link(path: Path, doc_output: Path, repo_root: Path) -> str:
    try:
        return Path(os.path.relpath(path.resolve(), doc_output.parent.resolve())).as_posix()
    except ValueError:
        return _display_path(path, repo_root)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence_record(
    *, evidence_id: str, path: Path, required: bool, role: str, repo_root: Path
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "evidence_id": evidence_id,
        "path": _display_path(path, repo_root),
        "required": required,
        "role": role,
        "present": path.is_file(),
    }
    if path.is_file():
        digest = _sha256_file(path)
        record.update(
            {
                "content_sha256": digest,
                "content_hash": f"sha256:{digest}",
                "size_bytes": path.stat().st_size,
            }
        )
        if path.suffix == ".json":
            payload = _load_json(path) or {}
            record["schema_version"] = payload.get("schema_version", "")
            record["status"] = payload.get("status", "")
    return record


def _strip_cell(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _split_markdown_row(line: str) -> list[str]:
    return [_strip_cell(cell) for cell in line.strip().strip("|").split("|")]


def _extract_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _split_markdown_row(line)
        if len(cells) >= 2 and cells[0] == field:
            return cells[1]
    return ""


def _source_ids_from_cell(cell: str) -> list[str]:
    source_ids: list[str] = []
    pattern = re.compile(
        r"(?P<prefix>(?:AIM120-(?:WF|TPC|TPC-REJ)|PHYS-BF)-)"
        r"(?P<suffixes>\d{3}(?:/\d{3})*)"
    )
    for match in pattern.finditer(cell):
        prefix = match.group("prefix")
        for suffix in match.group("suffixes").split("/"):
            source_ids.append(f"{prefix}{suffix}")
    return source_ids


def _warhead_rows(text: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _split_markdown_row(line)
        if len(cells) < 8 or cells[0] not in EXPECTED_ASSUMPTION_IDS:
            continue
        rows[cells[0]] = {
            "assumption_id": cells[0],
            "scope_claim": cells[1],
            "source_ids": _source_ids_from_cell(cells[2]),
            "third_party_candidates": cells[3],
            "consumed_by_surrogate": cells[4],
            "sensitivity_axis": cells[5],
            "forbidden_authority_claim": cells[6],
            "residual": cells[7],
        }
    return rows


PIN_COLUMNS = [
    "artifact_id",
    "source_id",
    "source_tier",
    "source_ref",
    "access_status",
    "artifact_status",
    "sha256",
    "retention_ref",
    "consumption_status",
    "candidate_use",
    "authority_boundary",
    "residuals",
]


def _pin_rows(text: str, residual_id: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _split_markdown_row(line)
        if len(cells) < len(PIN_COLUMNS):
            continue
        if not cells[0].startswith("PIN-") or residual_id not in cells[11]:
            continue
        rows[cells[0]] = dict(zip(PIN_COLUMNS, cells[: len(PIN_COLUMNS)]))
    return rows


def _residual_register_status(text: str, residual_id: str) -> dict[str, str]:
    for line in text.splitlines():
        if f"`{residual_id}`" not in line:
            continue
        cells = _split_markdown_row(line)
        if len(cells) >= 7:
            return {
                "residual_id": residual_id,
                "area": cells[1],
                "description": cells[2],
                "scope_impact": cells[3],
                "blocked_authority": cells[4],
                "close_condition": cells[5],
                "register_status": cells[6],
            }
    return {
        "residual_id": residual_id,
        "area": "",
        "description": "",
        "scope_impact": "",
        "blocked_authority": "",
        "close_condition": "",
        "register_status": "missing",
    }


def _check(check_id: str, summary: str, passed: bool) -> dict[str, Any]:
    return {"check_id": check_id, "summary": summary, "pass": bool(passed)}


def _all_authority_values_false(guards: dict[str, Any] | None) -> bool:
    if not guards:
        return False
    return not any(value is True for value in guards.values())


def _authority_guards() -> dict[str, bool]:
    return {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "stock_runtime_authority_granted": False,
        "runtime_descriptor_created": False,
        "runtime_authority_granted": False,
        "aim120c_warhead_authority_granted": False,
        "missile_specific_warhead_truth_granted": False,
        "variant_specific_warhead_mass_authority_granted": False,
        "tnt_equivalent_authority_granted": False,
        "fragment_pattern_authority_granted": False,
        "warhead_family_scope_promoted_to_truth": False,
        "toy_warhead_numeric_proxy_promoted_to_authority": False,
        "effect_scale_authority_granted": False,
        "effect_scale_authority_in_stock": False,
        "effect_scale_authority_released": False,
        "component_failure_probability_authority_granted": False,
        "component_failure_probability_authority_in_stock": False,
        "component_failure_probability_authority_released": False,
        "pk_authority_granted": False,
        "pk_authority_released": False,
        "deterministic_fuze_authority_granted": False,
        "deterministic_fuze_authority_released": False,
        "fuze_authority_granted": False,
        "formal_validation_manifest_promoted": False,
        "hard_gate_pass_is_release": False,
        "replacement_allowed": False,
    }


def _warhead_scope_review(warhead_text: str) -> dict[str, Any]:
    rows = _warhead_rows(warhead_text)
    consumed_rows = [rows.get(item, {}) for item in EXPECTED_CONSUMED_ASSUMPTION_IDS]
    non_release_rows = [
        rows.get(item, {}) for item in EXPECTED_NON_RELEASE_ASSUMPTION_IDS
    ]
    all_source_ids = sorted(
        {
            source_id
            for row in rows.values()
            for source_id in row.get("source_ids", [])
        }
    )

    checks = [
        _check(
            "RES004-SCOPE-001",
            "warhead scope manifest is frozen to Stage B effect-scale candidate review",
            _extract_field(warhead_text, "package_id") == PACKAGE_ID
            and _extract_field(warhead_text, "primary_release_scope")
            == "effect_scale_authority_only"
            and _extract_field(warhead_text, "weapon_class") == "AIM-120C-class"
            and _extract_field(warhead_text, "weapon_family")
            == "blast_fragmentation",
        ),
        _check(
            "RES004-SCOPE-002",
            "expected warhead assumption rows are present and only family/toy/method rows are consumed",
            list(rows) == EXPECTED_ASSUMPTION_IDS
            and [
                row.get("assumption_id")
                for row in rows.values()
                if row.get("consumed_by_surrogate") == "yes"
            ]
            == EXPECTED_CONSUMED_ASSUMPTION_IDS
            and all(
                row.get("consumed_by_surrogate")
                in {
                    "loaded_but_not_release_gating",
                    "no_numeric_consumption",
                    "no_for_stage_b_release",
                    "no",
                }
                for row in non_release_rows
            ),
        ),
        _check(
            "RES004-SCOPE-003",
            "family label, toy numeric proxy, and public method route remain separated",
            rows.get("WAR-001", {}).get("sensitivity_axis")
            == "family gate / vocabulary"
            and rows.get("WAR-002", {}).get("sensitivity_axis")
            == "blast scaled-distance proxy, toy fragment-count / energy proxy"
            and rows.get("WAR-005", {}).get("sensitivity_axis")
            == "method route, monotonicity, unit and uncertainty hygiene"
            and "toy input" in rows.get("WAR-002", {}).get("scope_claim", "")
            and "toy proxy" in rows.get("WAR-005", {}).get("scope_claim", ""),
        ),
        _check(
            "RES004-SCOPE-004",
            "third-party mass claims and community/game/forum values are sanity-only or rejected",
            rows.get("WAR-006", {}).get("consumed_by_surrogate")
            == "no_for_stage_b_release"
            and rows.get("WAR-007", {}).get("third_party_candidates", "").startswith(
                "rejected:"
            )
            and "DCS" in rows.get("WAR-007", {}).get(
                "forbidden_authority_claim", ""
            ),
        ),
        _check(
            "RES004-SCOPE-005",
            "the manifest explicitly forbids variant-specific warhead truth, fuze truth, and Pk expansion",
            "AIM-120C-7/C-8 warhead or fuze truth" in warhead_text
            and "deterministic fuze trigger radius" in warhead_text
            and "`Pk`" in warhead_text
            and "not enough for warhead authority" in warhead_text,
        ),
    ]
    return {
        "status": (
            "stage_b_warhead_family_scope_surface_bounded"
            if all(row["pass"] for row in checks)
            else "stage_b_warhead_family_scope_surface_incomplete"
        ),
        "weapon_class": _extract_field(warhead_text, "weapon_class"),
        "weapon_family": _extract_field(warhead_text, "weapon_family"),
        "consumed_by_surrogate_assumptions": EXPECTED_CONSUMED_ASSUMPTION_IDS,
        "non_release_assumptions": EXPECTED_NON_RELEASE_ASSUMPTION_IDS,
        "source_ids_seen_in_scope_manifest": all_source_ids,
        "row_findings": rows,
        "checks": checks,
    }


def _source_pin_review(*, pin_text: str, source_text: str) -> dict[str, Any]:
    pins = _pin_rows(pin_text, "RES-004")
    expected_pins_present = [pin for pin in EXPECTED_RES004_PIN_IDS if pin in pins]
    release_consumed_pin_ids = [
        pin_id
        for pin_id, row in pins.items()
        if row["consumption_status"]
        in {
            "release_retained_benchmark_input",
            "release_grade_benchmark_input",
            "consumed_for_release_benchmark",
        }
    ]
    source_presence = {
        source_id: f"`{source_id}`" in source_text for source_id in EXPECTED_SOURCE_IDS
    }
    authority_boundaries = {
        pin_id: row["authority_boundary"] for pin_id, row in pins.items()
    }
    checks = [
        _check(
            "RES004-SRC-001",
            "required RES-004 source ledger IDs are present",
            all(source_presence.values())
            and "`authority_status=non-authoritative`" in source_text
            and "所有条目默认" in source_text,
        ),
        _check(
            "RES004-SRC-002",
            "artifact pin manifest contains official public pins plus sanity/rejection pins for RES-004",
            expected_pins_present == EXPECTED_RES004_PIN_IDS
            and pins["PIN-AIM120-001"]["artifact_status"] == "official_public_pdf"
            and pins["PIN-AIM120-002"]["artifact_status"] == "official_public_pdf"
            and pins["PIN-AIM120-TPC-001"]["consumption_status"] == "sanity_only"
            and pins["PIN-AIM120-TPC-REJ"]["consumption_status"] == "rejected",
        ),
        _check(
            "RES004-SRC-003",
            "no RES-004 pin is consumed as a release-grade benchmark or runtime row",
            release_consumed_pin_ids == []
            and all(
                pins[pin_id]["consumption_status"]
                in {"acquired_for_candidate", "sanity_only", "rejected"}
                for pin_id in expected_pins_present
            ),
        ),
        _check(
            "RES004-SRC-004",
            "source and pin boundaries forbid fuze/Pk and AIM-120C mass truth",
            "不能导出 trigger radius" in source_text
            and "不得作为 calibrated C 型 mass" in source_text
            and "trigger threshold" in authority_boundaries.get("PIN-AIM120-001", "")
            and "AIM-120C mass truth" in authority_boundaries.get(
                "PIN-AIM120-TPC-001", ""
            ),
        ),
    ]
    return {
        "status": (
            "source_pin_boundary_bounded"
            if all(row["pass"] for row in checks)
            else "source_pin_boundary_incomplete"
        ),
        "source_presence": source_presence,
        "res004_pin_ids": expected_pins_present,
        "release_consumed_pin_ids": release_consumed_pin_ids,
        "pin_consumption_status": {
            pin_id: row["consumption_status"] for pin_id, row in pins.items()
        },
        "authority_boundaries": authority_boundaries,
        "checks": checks,
    }


def _provenance_review(payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    res004 = payload.get("residual_status", {}).get("RES-004", {})
    release_blockers = payload.get("release_blockers", {}).get("RES-004", [])
    checks = [
        _check(
            "RES004-PROV-001",
            "geometry/warhead provenance gate is present and keeps RES-004 non-authoritative",
            payload.get("schema_version")
            == "a2.geometry_warhead_row_provenance_gate.v1"
            and payload.get("status")
            == "blocked_non_authoritative_geometry_warhead_row_provenance_candidate",
        ),
        _check(
            "RES004-PROV-002",
            "provenance gate marks the author-side RES-004 subslice ready but not release-grade",
            res004.get("author_side_subslice_ready") is True
            and res004.get("release_grade") is False
            and res004.get("closed_by_this_gate") is False,
        ),
        _check(
            "RES004-PROV-003",
            "provenance gate preserves blockers for model-specific warhead truth and toy numeric inputs",
            any("variant-specific warhead internals" in blocker for blocker in release_blockers)
            and any("repo warhead.mass_kg" in blocker for blocker in release_blockers)
            and any("third-party" in blocker for blocker in release_blockers),
        ),
        _check(
            "RES004-PROV-004",
            "provenance gate grants no warhead, stock, effect-scale, component, Pk, or fuze authority",
            _all_authority_values_false(payload.get("authority_guard")),
        ),
    ]
    return {
        "status": (
            "row_provenance_interlock_preserved"
            if all(row["pass"] for row in checks)
            else "row_provenance_interlock_incomplete"
        ),
        "upstream_status": payload.get("status", "missing"),
        "upstream_res004_status": res004,
        "release_blockers_preserved": release_blockers,
        "checks": checks,
    }


def _mechanism_source_interlock(payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    results = payload.get("current_gate_results", {})
    subitems = payload.get("closed_author_side_subitems", {}).get("RES-004", [])
    guards = payload.get("non_authoritative_guards", {})
    checks = [
        _check(
            "RES004-MECH-001",
            "mechanism/source closeout gate records RES-004 author-side readiness",
            payload.get("schema_version") == "a2.mechanism_source_closeout_gate.v1"
            and results.get("RES-004") == "blocked_author_side_review_ready",
        ),
        _check(
            "RES004-MECH-002",
            "mechanism/source closeout separates family label from variant-specific truth",
            any("family label is separated" in item for item in subitems)
            and any("sanity-only or rejected" in item for item in subitems),
        ),
        _check(
            "RES004-MECH-003",
            "mechanism/source closeout keeps deterministic fuze and Pk outside this gate",
            payload.get("remaining_release_grade_paths", {})
            .get("RES-004", ["", ""])[-1]
            == "keep deterministic fuze and Pk outside this gate unless a separate evidence chain exists",
        ),
        _check(
            "RES004-MECH-004",
            "mechanism/source closeout grants no stock, mechanism, effect-scale, component, Pk, or fuze authority",
            _all_authority_values_false(guards),
        ),
    ]
    return {
        "status": (
            "mechanism_source_interlock_bounded"
            if all(row["pass"] for row in checks)
            else "mechanism_source_interlock_incomplete"
        ),
        "upstream_status": payload.get("status", "missing"),
        "upstream_res004_result": results.get("RES-004", "missing"),
        "closed_author_side_subitems": subitems,
        "checks": checks,
    }


def _minimum_gap_list(
    *,
    closeout_allowed: bool,
    failed_checks: list[dict[str, Any]],
    missing: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if closeout_allowed:
        return [
            {
                "gap_id": "RES004-GLOBAL-001",
                "owner": "future_warhead_truth_evidence_owner",
                "minimum_next_step": (
                    "bind public/authorized variant-specific warhead mass, TNT equivalent, "
                    "fragment pattern, casing, and sensitivity envelope before any AIM-120C "
                    "warhead truth or runtime row claim"
                ),
            },
            {
                "gap_id": "RES004-FUZE-001",
                "owner": "future_fuze_or_kill_chain_package_owner",
                "minimum_next_step": (
                    "keep deterministic fuze trigger, delay, reliability, target signature, "
                    "and Pk outside this package unless a separate evidence chain exists"
                ),
            },
            {
                "gap_id": "RES004-INTEGRATION-001",
                "owner": "main_thread_acceptance_owner",
                "minimum_next_step": (
                    "if accepted, update the residual register only as a Stage B "
                    "AIM-120C-class blast-fragmentation family-scope narrow closeout"
                ),
            },
        ]

    gaps = [
        {
            "gap_id": f"missing:{row['evidence_id']}",
            "owner": "res004_closeout_worker_or_evidence_owner",
            "minimum_next_step": f"restore required evidence at {row['path']}",
        }
        for row in missing
    ]
    gaps.extend(
        {
            "gap_id": f"failed:{row['check_id']}",
            "owner": "res004_closeout_worker_or_upstream_gate_owner",
            "minimum_next_step": row["summary"],
        }
        for row in failed_checks
    )
    return gaps


def generate_res004_warhead_scope_closeout_gate(
    *,
    repo_root: Path = REPO_ROOT,
    package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
    refs = _evidence_refs(package_dir=package_dir, repo_root=repo_root)
    consumed_evidence = [
        _evidence_record(
            evidence_id=evidence_id,
            path=path,
            required=required,
            role=role,
            repo_root=repo_root,
        )
        for evidence_id, (path, required, role) in refs.items()
    ]
    missing_evidence = [
        row for row in consumed_evidence if row["required"] and not row["present"]
    ]

    residual_text = _read_text(refs["residual_register"][0])
    warhead_text = _read_text(refs["warhead_scope_and_sensitivity"][0])
    pin_text = _read_text(refs["artifact_pin_manifest"][0])
    source_text = _read_text(refs["warhead_source_ledger"][0])
    provenance_payload = _load_json(refs["geometry_warhead_row_provenance_gate"][0])
    mechanism_payload = _load_json(refs["mechanism_source_closeout_gate"][0])

    scope_review = _warhead_scope_review(warhead_text)
    source_pin_review = _source_pin_review(pin_text=pin_text, source_text=source_text)
    provenance_review = _provenance_review(provenance_payload)
    mechanism_interlock = _mechanism_source_interlock(mechanism_payload)
    all_checks = (
        scope_review["checks"]
        + source_pin_review["checks"]
        + provenance_review["checks"]
        + mechanism_interlock["checks"]
    )
    failed_checks = [row for row in all_checks if not row["pass"]]
    closeout_allowed = not missing_evidence and not failed_checks

    decision_status = (
        "res004_stage_b_effect_scale_warhead_family_scope_closeout_pass_release_blocked"
        if closeout_allowed
        else "res004_warhead_scope_closeout_fail_closed"
    )

    return {
        "package_id": PACKAGE_ID,
        "schema_version": GATE_SCHEMA_VERSION,
        "generated_on": GENERATED_ON,
        "status": decision_status,
        "worker_identity": {
            "worker_id": WORKER_ID,
            "nickname": "res004-warhead-scope-closeout-worker",
            "independence_class": "project_internal_closeout_worker",
            "external_validation_claimed": False,
        },
        "review_target": "RES-004_warhead_scope_closeout",
        "release_target": (
            "stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope_only"
        ),
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "candidate_scope_label": "near_miss_0_35m",
            "stage_b_scope": "effect_scale_only",
        },
        "consumed_evidence": consumed_evidence,
        "missing_evidence": missing_evidence,
        "stage_b_scope_review": scope_review,
        "source_pin_review": source_pin_review,
        "provenance_interlock": provenance_review,
        "mechanism_source_interlock": mechanism_interlock,
        "residual_register_snapshot": _residual_register_status(
            residual_text, "RES-004"
        ),
        "residual_closeout_decisions": {
            "RES-004": {
                "stage_b_effect_scale_warhead_family_scope": (
                    "closed_narrow_non_authoritative"
                    if closeout_allowed
                    else "fail_closed"
                ),
                "closed_residual_subscope": (
                    "stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope"
                    if closeout_allowed
                    else "none"
                ),
                "missile_specific_aim120c_warhead_truth": "forbidden",
                "variant_specific_mass_tnt_fragment_pattern": "blocked",
                "toy_numeric_proxy_authority": "not_granted",
                "deterministic_fuze_dependency": "forbidden",
                "pk_dependency": "forbidden",
                "component_probability_dependency": "blocked",
                "residual_register_edit_required_by_this_gate": False,
                "main_thread_register_integration_note": (
                    "may mark only the Stage B AIM-120C-class blast-fragmentation "
                    "family-scope subscope as closed if accepted; do not mark "
                    "variant-specific warhead truth, fuze, Pk, component probability, "
                    "or runtime authority closed"
                ),
            }
        },
        "closeout_decision": {
            "stage_b_effect_scale_warhead_family_scope_closeout_complete": closeout_allowed,
            "stage_b_effect_scale_closeout_is_release_authority": False,
            "aim120c_specific_warhead_truth_closeout_complete": False,
            "variant_specific_warhead_mass_or_fragment_pattern_closeout_complete": False,
            "deterministic_fuze_closeout_complete": False,
            "component_probability_release_ready": False,
            "closed_residual_ids_by_this_gate": [],
            "closed_residual_subscopes_by_this_gate": (
                [
                    "RES-004:stage_b_effect_scale_aim120c_class_blast_fragmentation_family_scope"
                ]
                if closeout_allowed
                else []
            ),
            "release_ready": False,
            "release_blocked": True,
            "authority_release_included": False,
        },
        "authority_guards": _authority_guards(),
        "explicit_boundaries": [
            "The closeout is limited to Stage B effect-scale AIM-120C-class blast-fragmentation family scope.",
            "AIM-120C-class is a family-level candidate label, not AIM-120C-7/C-8 warhead truth.",
            "repo warhead.mass_kg and lethal_radius remain toy inputs/bookkeeping, not calibrated AIM-120C mass, TNT equivalent, fragment pattern, or kill radius.",
            "third-party 40 lb / 18 kg claims remain sanity-only and community/forum/game values remain rejected.",
            "No stock descriptor, runtime authority, effect-scale authority, component probability, Pk, deterministic fuze, or formal validation promotion is granted.",
            "Stage C remains blocked until independent component fragility truth and probability uncertainty evidence exist.",
        ],
        "minimum_gap_list": _minimum_gap_list(
            closeout_allowed=closeout_allowed,
            failed_checks=failed_checks,
            missing=missing_evidence,
        ),
        "behavior_risks": [
            "AIM-120C-class family scope may be over-read as variant-specific AIM-120C warhead truth",
            "repo toy warhead mass or lethal-radius fields may be over-read as calibrated runtime rows",
            "third-party mass clusters or forum/game values may be over-read as source-backed parameters",
            "Stage B narrow closeout may be mistaken for deterministic fuze, Pk, or component-probability authority",
        ],
        "integration_notes": [
            "This gate supersedes RES-004 only for the bounded Stage B warhead-family scope subscope.",
            "Existing geometry/warhead provenance and mechanism/source gates remain valid and still block warhead truth authority.",
            "Main-thread acceptance should preserve RES-005/006 and Stage C blockers unless their own gates close.",
            "RES-013 Pk and RES-014 deterministic-fuze boundaries remain outside this package.",
        ],
    }


def _manifest_payload(
    *, artifact: dict[str, Any], output_dir: Path, repo_root: Path
) -> dict[str, Any]:
    gate_path = output_dir / "res004_warhead_scope_closeout_gate.json"
    return {
        "package_id": PACKAGE_ID,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_on": GENERATED_ON,
        "status": "res004_warhead_scope_closeout_retained_release_blocked",
        "artifacts": [
            {
                "artifact_key": "res004_warhead_scope_closeout_gate",
                "path": _display_path(gate_path, repo_root),
                "content_sha256": _sha256_file(gate_path),
                "size_bytes": gate_path.stat().st_size,
            }
        ],
        "closeout_decision": artifact["closeout_decision"],
        "authority_guards": artifact["authority_guards"],
        "worker_identity": artifact["worker_identity"],
    }


def _render_doc(
    *,
    artifact: dict[str, Any],
    manifest: dict[str, Any],
    gate_sha256: str,
    manifest_sha256: str,
    output_dir: Path,
    doc_output: Path,
    repo_root: Path,
) -> str:
    res004 = artifact["residual_closeout_decisions"]["RES-004"]
    guards = artifact["authority_guards"]
    guard_rows = "\n".join(
        f"| `{key}` | `{str(value).lower()}` |" for key, value in guards.items()
    )
    evidence_rows = "\n".join(
        f"| `{row['evidence_id']}` | `{row['present']}` | `{row.get('status', 'n/a')}` | `{row['path']}` |"
        for row in artifact["consumed_evidence"]
    )
    gap_rows = "\n".join(
        f"| `{row['gap_id']}` | `{row['owner']}` | {row['minimum_next_step']} |"
        for row in artifact["minimum_gap_list"]
    )
    boundary_rows = "\n".join(
        f"- {boundary}" for boundary in artifact["explicit_boundaries"]
    )
    return f"""# Validation RES-004 Warhead Scope Closeout Gate - 2026-05-31

状态：`generated_from_res004_warhead_scope_closeout_gate / non-authoritative / release_blocked`。

本文记录 `RES-004 warhead scope` 的窄域 closeout。该 gate 只允许关闭 Stage B `effect_scale` 的 `AIM-120C-class / blast_fragmentation` family-scope 子范围；不关闭 AIM-120C 具体型号战斗部真值、toy numeric authority、deterministic fuze、Pk、component probability 或 runtime authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `{artifact['package_id']}` |
| `schema_version` | `{artifact['schema_version']}` |
| `tool_ref` | [a2_blastfrag_res004_warhead_scope_closeout_gate.py]({_doc_link(repo_root / "tools" / "maintenance" / "a2_blastfrag_res004_warhead_scope_closeout_gate.py", doc_output, repo_root)}) |
| `retained_artifact` | [{output_dir.name}/res004_warhead_scope_closeout_gate.json]({_doc_link(output_dir / 'res004_warhead_scope_closeout_gate.json', doc_output, repo_root)}) |
| `retained_artifact_sha256` | `{gate_sha256}` |
| `manifest` | [{output_dir.name}/manifest.json]({_doc_link(output_dir / 'manifest.json', doc_output, repo_root)}) |
| `manifest_sha256` | `{manifest_sha256}` |
| `overall_status` | `{artifact['status']}` |
| `manifest_status` | `{manifest['status']}` |

## 2. Decision

| 字段 | 值 |
|---|---|
| `stage_b_effect_scale_warhead_family_scope` | `{res004['stage_b_effect_scale_warhead_family_scope']}` |
| `closed_residual_subscope` | `{res004['closed_residual_subscope']}` |
| `missile_specific_aim120c_warhead_truth` | `{res004['missile_specific_aim120c_warhead_truth']}` |
| `variant_specific_mass_tnt_fragment_pattern` | `{res004['variant_specific_mass_tnt_fragment_pattern']}` |
| `deterministic_fuze_dependency` | `{res004['deterministic_fuze_dependency']}` |
| `pk_dependency` | `{res004['pk_dependency']}` |
| `component_probability_dependency` | `{res004['component_probability_dependency']}` |
| `release_ready` | `{str(artifact['closeout_decision']['release_ready']).lower()}` |
| `release_blocked` | `{str(artifact['closeout_decision']['release_blocked']).lower()}` |

当前可审计结论：

> `RES-004 is narrowly closed only for Stage B effect-scale AIM-120C-class blast-fragmentation family scope; missile-specific warhead truth, toy numeric authority, deterministic fuze, Pk, component probability, stock runtime and formal validation promotion remain blocked`.

## 3. Consumed Evidence

| evidence | present | upstream status | path |
|---|---:|---|---|
{evidence_rows}

## 4. Non-Authoritative Guards

| guard | current value |
|---|---:|
{guard_rows}

## 5. Boundaries

{boundary_rows}

## 6. Remaining Paths

| gap | owner | minimum next step |
|---|---|---|
{gap_rows}
"""


def write_retained_outputs(
    *,
    artifact: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_output: Path = DEFAULT_DOC_OUTPUT,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_path = output_dir / "res004_warhead_scope_closeout_gate.json"
    gate_path.write_text(_canonical_json(artifact) + "\n", encoding="utf-8")
    gate_sha256 = _sha256_file(gate_path)

    manifest = _manifest_payload(
        artifact=artifact, output_dir=output_dir, repo_root=repo_root
    )
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
    manifest_sha256 = _sha256_file(manifest_path)

    doc_output.parent.mkdir(parents=True, exist_ok=True)
    doc_output.write_text(
        _render_doc(
            artifact=artifact,
            manifest=manifest,
            gate_sha256=gate_sha256,
            manifest_sha256=manifest_sha256,
            output_dir=output_dir,
            doc_output=doc_output,
            repo_root=repo_root,
        ),
        encoding="utf-8",
    )

    return {
        "status": artifact["status"],
        "gate_path": _display_path(gate_path, repo_root),
        "gate_sha256": gate_sha256,
        "manifest_path": _display_path(manifest_path, repo_root),
        "manifest_sha256": manifest_sha256,
        "doc_path": _display_path(doc_output, repo_root),
        "closeout_decision": artifact["closeout_decision"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the RES-004 warhead scope narrow closeout gate."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-output", type=Path, default=DEFAULT_DOC_OUTPUT)
    args = parser.parse_args(argv)

    artifact = generate_res004_warhead_scope_closeout_gate()
    summary = write_retained_outputs(
        artifact=artifact,
        output_dir=args.output_dir,
        doc_output=args.doc_output,
    )
    print(_canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
