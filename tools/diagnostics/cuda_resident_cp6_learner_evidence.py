"""CP-6 learner-consumption evidence: declared-generation report validation.

The four CP-6 campaign reports were captured with the learner mode appended to
the frozen v1 report shape while still carrying the v1 schema id, so the
frozen four-mode validator rightly rejects them. This module owns that
declared generation: it validates the learner extension itself (the fifth mode
entry and its rows), strips the extension, and delegates everything else to
the untouched v1 validator, so the frozen CR2-6b/CP-8 validation surface never
drifts. The learner identities are parsed from the C++ contract, which stays
their single owner, and the tracked evidence package hash-pins each report to
the generation it is validated under.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    from tools.diagnostics import cuda_resident_cr2_matrix_probe as matrix_probe
    from tools.diagnostics import cuda_resident_retained_evidence_paths as retained_paths
except ModuleNotFoundError:
    import cuda_resident_cr2_matrix_probe as matrix_probe
    import cuda_resident_retained_evidence_paths as retained_paths


EVIDENCE_SCHEMA = "cuda_resident.cp6.learner_consumption_evidence.v1"
DECLARED_GENERATION = "cr2_matrix_probe.v1_schema_with_learner_mode_appended"
FORWARD_GENERATION = "cp6_matrix_probe.v2_self_declared"
CONTRACT_RELATIVE = "src/runtime/contracts/cuda_resident_learner_consumption_contract.h"
LEARNER_MODE_KEYS = {"mode_id", "host_export", "device_consumer", "learner_consumer", "cpu_available"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class LearnerEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LearnerEvidenceError(message)


def contract_identities(root: Path) -> dict[str, str]:
    """The C++ contract is the single owner of the learner identities."""
    text = (root / CONTRACT_RELATIVE).read_text(encoding="utf-8")
    identities: dict[str, str] = {}
    for key, symbol in (
        ("mode_id", "kLearnerConsumerModeIdNoExport"),
        ("forward_probe_schema", "kLearnerProbeSchemaV2"),
    ):
        match = re.search(symbol + r"\s*=\s*\n?\s*\"([^\"]+)\"", text)
        _require(match is not None, f"learner contract does not define {symbol}")
        identities[key] = match.group(1)
    return identities


def registered_generations(root: Path) -> dict[str, str]:
    """Each registered report generation maps to exactly one schema id, so a
    relabeled report can never ride into a package declaring another one."""
    identities = contract_identities(root)
    return {
        DECLARED_GENERATION: matrix_probe.SCHEMA,
        FORWARD_GENERATION: identities["forward_probe_schema"],
    }


def validate_learner_report(
    report: dict[str, Any], root: Path, *, require_production: bool, declared_generation: str
) -> None:
    """Validate a five-mode learner report against its declared generation.

    The learner extension is checked here; the remainder must be exactly the
    frozen v1 shape, enforced by delegating a stripped copy to the frozen
    validator.
    """
    generations = registered_generations(root)
    _require(
        declared_generation in generations,
        f"unknown declared report generation: {declared_generation!r}",
    )
    identities = contract_identities(root)
    mode_id = identities["mode_id"]
    _require(isinstance(report, dict), "learner report must be an object")
    _require(
        report.get("schema_version") == generations[declared_generation],
        "learner report schema does not match its declared generation",
    )

    modes = report.get("modes")
    _require(isinstance(modes, list) and len(modes) == len(matrix_probe.MODES) + 1,
             "learner report must carry exactly one appended mode")
    learner_entries = [entry for entry in modes if entry.get("mode_id") == mode_id]
    _require(len(learner_entries) == 1, "learner mode entry is missing or duplicated")
    _require(
        learner_entries[0]
        == {
            "mode_id": mode_id,
            "host_export": False,
            "device_consumer": True,
            "learner_consumer": True,
            "cpu_available": False,
        },
        "learner mode entry drifted",
    )

    rows = report.get("rows")
    _require(isinstance(rows, list), "learner report rows must be an array")
    learner_rows = [row for row in rows if row.get("mode_id") == mode_id]
    world_counts = report.get("world_counts")
    _require(isinstance(world_counts, list) and bool(world_counts), "world counts invalid")
    _require(
        sorted(row.get("world_count") for row in learner_rows) == sorted(world_counts),
        "learner rows do not cover the world matrix exactly once",
    )
    lane = report.get("lane")
    sibling = {
        (row.get("world_count"), row.get("mode_id")): row
        for row in rows
        if row.get("mode_id") == "no_export_device_consumer"
    }
    protocol = report.get("protocol")
    for row in learner_rows:
        _require(set(row) == matrix_probe.ROW_KEYS, "learner row schema drifted")
        _require(row.get("host_export") is False, "learner row host export drifted")
        _require(row.get("device_consumer") is True, "learner row consumer flag drifted")
        _require(row.get("promotion_eligible") is False, "learner row permits promotion")
        partner = sibling.get((row.get("world_count"), "no_export_device_consumer"))
        _require(partner is not None, "learner row lacks its device-consumer sibling")
        _require(
            row.get("trace_signature") == partner.get("trace_signature"),
            "learner row trace signature diverges from its sibling",
        )
        if lane == "cuda_resident":
            _require(row.get("available") is True, "CUDA learner row must be available")
            matrix_probe._validate_available_row(row, lane, protocol, True)
            _require(
                row["reset_determinism"]["digest"]
                == partner["reset_determinism"]["digest"],
                "learner row reset digest diverges from its sibling",
            )
        else:
            _require(row.get("available") is False, "CPU learner row must be unavailable")
            _require(
                row.get("unavailable_reason")
                == "cpu_reference_has_no_device_observation_consumer",
                "CPU learner N/A reason drifted",
            )

    stripped = copy.deepcopy(report)
    stripped["schema_version"] = matrix_probe.SCHEMA
    stripped["modes"] = [entry for entry in stripped["modes"] if entry["mode_id"] != mode_id]
    stripped["rows"] = [row for row in stripped["rows"] if row["mode_id"] != mode_id]
    matrix_probe.validate_report(stripped, require_production=require_production)


def _verify_report_descriptor(root: Path, descriptor: object, label: str) -> dict[str, Any]:
    _require(
        isinstance(descriptor, dict)
        and set(descriptor) == {"path", "lane", "bytes", "sha256"},
        f"{label} descriptor schema drifted",
    )
    _require(
        descriptor["lane"] in {"flecs_cpu_reference", "cuda_resident"},
        f"{label} lane invalid",
    )
    path = root / retained_paths.physical_relative(str(descriptor["path"]))
    _require(path.is_file(), f"{label} report is missing")
    payload = path.read_bytes()
    _require(
        type(descriptor["bytes"]) is int and descriptor["bytes"] == len(payload),
        f"{label} size mismatch",
    )
    _require(
        type(descriptor["sha256"]) is str
        and SHA256.fullmatch(descriptor["sha256"]) is not None
        and hashlib.sha256(payload).hexdigest() == descriptor["sha256"],
        f"{label} hash mismatch",
    )
    report = json.loads(payload.decode("utf-8"))
    _require(report.get("lane") == descriptor["lane"], f"{label} lane mismatch")
    return report


def _committed_canonical_bytes(root: Path, commit: str, recorded: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{recorded}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    _require(completed.returncode == 0, f"source input is not in the capture commit: {recorded}")
    return completed.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _verify_source_input(root: Path, commit: str, descriptor: object, label: str) -> None:
    _require(
        isinstance(descriptor, dict)
        and set(descriptor) == {"path", "canonicalization", "canonical_bytes", "sha256"},
        f"{label} source descriptor schema drifted",
    )
    _require(descriptor["canonicalization"] == "utf8_lf", f"{label} canonicalization drifted")
    payload = _committed_canonical_bytes(root, commit, str(descriptor["path"]))
    _require(
        type(descriptor["canonical_bytes"]) is int
        and descriptor["canonical_bytes"] == len(payload)
        and type(descriptor["sha256"]) is str
        and hashlib.sha256(payload).hexdigest() == descriptor["sha256"],
        f"{label} does not match the capture commit's source",
    )


def validate_evidence(package: dict[str, Any], root: Path) -> None:
    keys = {
        "schema_version",
        "iteration",
        "evidence_date",
        "declared_report_generation",
        "learner_mode_id",
        "forward_probe_schema",
        "source_commit",
        "source_state",
        "source_inputs",
        "validator_source",
        "reports",
        "interpretation",
        "gates",
    }
    _require(isinstance(package, dict) and set(package) == keys,
             "learner evidence top-level schema drifted")
    _require(package["schema_version"] == EVIDENCE_SCHEMA, "learner evidence schema mismatch")
    _require(package["iteration"] == "CP-6", "learner evidence iteration drifted")
    declared = package["declared_report_generation"]
    _require(
        declared in registered_generations(root),
        f"unknown declared report generation: {declared!r}",
    )
    identities = contract_identities(root)
    _require(package["learner_mode_id"] == identities["mode_id"],
             "learner evidence mode id diverges from the contract owner")
    _require(
        package["forward_probe_schema"] == identities["forward_probe_schema"],
        "learner evidence forward schema diverges from the contract owner",
    )
    commit = package["source_commit"]
    _require(
        type(commit) is str and COMMIT.fullmatch(commit) is not None,
        "learner evidence source commit invalid",
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    _require(ancestor.returncode == 0, "source commit is not an ancestor of HEAD")
    _require(
        package["source_state"]
        == "captured_from_the_worktree_subsequently_committed_as_source_commit",
        "learner evidence source state drifted",
    )
    source_inputs = package["source_inputs"]
    expected_sources = {
        "learner_contract",
        "consumer_implementation",
        "matrix_session",
        "matrix_probe",
    }
    _require(
        isinstance(source_inputs, dict) and set(source_inputs) == expected_sources,
        "learner evidence source-input inventory drifted",
    )
    for name, descriptor in source_inputs.items():
        _verify_source_input(root, commit, descriptor, name)
    validator = package["validator_source"]
    _require(
        isinstance(validator, dict)
        and set(validator) == {"path", "canonicalization", "canonical_bytes", "sha256"}
        and validator["path"] == "tools/diagnostics/cuda_resident_cp6_learner_evidence.py"
        and validator["canonicalization"] == "utf8_lf"
        and type(validator["canonical_bytes"]) is int
        and type(validator["sha256"]) is str
        and SHA256.fullmatch(validator["sha256"]) is not None,
        "learner evidence validator descriptor drifted",
    )
    reports = package["reports"]
    expected_reports = {
        "cpu_campaign1",
        "cuda_campaign1",
        "cuda_campaign2",
        "cpu_campaign2",
    }
    _require(isinstance(reports, dict) and set(reports) == expected_reports,
             "learner evidence report inventory drifted")
    for name, descriptor in reports.items():
        report = _verify_report_descriptor(root, descriptor, name)
        validate_learner_report(
            report, root, require_production=True, declared_generation=declared
        )
    interpretation = package["interpretation"]
    _require(
        isinstance(interpretation, dict)
        and interpretation.get("gate") == "G-C"
        and interpretation.get("cost_claim")
        == "within_host_run_to_run_noise_no_consistent_penalty"
        and interpretation.get("comparability")
        == "frozen_modes_unchanged_learner_mode_appended_behind_explicit_flag",
        "learner evidence interpretation drifted",
    )
    gates = package["gates"]
    expected_gates = {
        "cp6_learner_evidence_complete": True,
        "maintained_claim_allowed": False,
        "promotion_allowed": False,
        "public_support_enabled": False,
        "tuning_authorized": False,
    }
    _require(
        isinstance(gates, dict)
        and set(gates) == set(expected_gates)
        and all(gates[key] is value for key, value in expected_gates.items()),
        "learner evidence gates drifted",
    )
