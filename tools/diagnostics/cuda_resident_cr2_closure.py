from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "cuda_resident.program2_closure.v1"
CLOSURE_ID = "cr2_7.closed_without_promotion.cuda_resident.20260805"
BASELINE = "395e02b7dfeaa87baedb2611ec503d14ab137ce3"
PARENT_CLOSURE = "935926e83b18187c79a6e0be2ca010276c1a6fc4"
PRE_CLOSURE_HEAD = "356bcd56a61e40f1327d16b6a2dda335d7fdd553"
CLOSURE_COMMIT = "7efd36033c22a613bf7368bf0aa6fe8320e60e12"
BRANCH = "codex/cuda-resident-runtime-program-2"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")

ACCEPTED_COMMITS = {
    "CR2-0": "2f34fac6ea5ca27b24aa06246ec5d2cefd3725a0",
    "CR2-1": "db7e6ad4d32e31ac66df88672f17a95a1abf04e8",
    "CR2-2a": "bf6950714085371e011859f055d920854f5dc226",
    "CR2-2p": "dee02146e0f43b9424bebf94bbdad8672273bd59",
    "CR2-2b": "607c1f33ae5dfbc2ab6182dfc5ec0033a14a8def",
    "CR2-3": "7da41a2a4721b18cf488025a34cd8badc2b7135d",
    "CR2-4a": "d778c67c460d1c24d2c287ca7ac9c99136fe1f80",
    "CR2-4b": "08b48f299484428e7297f328ca860f8fadc31cc4",
    "CR2-5a": "6d7ec7ddbf4163436de6a2db3d2e13829227d1f8",
    "CR2-5b": "05b05c5a1f7968c603a4a933531bb52bdc30b9c4",
    "CR2-6a": "0c24a07549e238222741da6b20100537e7a9be22",
    "CR2-6b": PRE_CLOSURE_HEAD,
}

EXPECTED_DECISION = {
    "closure_disposition": "closed_without_promotion",
    "candidate_status": "retained_unmaintained_research_second_backend",
    "promotion_authorization_recorded": False,
    "promotion_allowed": False,
    "integration_plan_authorized": False,
    "runtime_selection_allowed": False,
    "runtime_mutation_allowed": False,
    "support_projection_allowed": False,
    "tuning_allowed": False,
    "reopen_requires_new_explicit_program": True,
}

EXPECTED_GATES = {
    "common_spi_full_window_available": True,
    "device_consumer_boundary_available": True,
    "selected_slice_parity_complete": True,
    "resource_static_topology_complete": True,
    "real_counter_attempt_documented": True,
    "achieved_counter_gate_complete": False,
    "production_matrix_complete": True,
    "small_batch_selection_advisory_complete": True,
    "maintained_claim_allowed": False,
    "public_support_enabled": False,
    "tuning_authorized": False,
    "promotion_allowed": False,
    "promotion_prerequisites_complete": False,
    "blocking_conditions": [
        "achieved_hardware_counters_unavailable:ERR_NVGPUCTRPERM",
        "promotion_authorization_absent",
        "integration_plan_absent",
    ],
}

EXPECTED_SELECTION = {
    "status": "experimental_advisory_only_not_runtime_selector",
    "maintained_default_backend": "flecs_cpu_reference",
    "measured_world_counts": [1, 4, 16, 64, 256],
    "world_1_common_modes": "flecs_cpu_reference",
    "world_4_no_export": "cuda_resident",
    "world_4_host_export": "flecs_cpu_reference_with_cuda_median_throughput_opt_in",
    "world_16_64_256_common_modes": "cuda_resident",
    "device_consumer_modes": "cuda_resident_required_without_cpu_comparison",
    "unmeasured_world_counts": "unclassified_no_extrapolation",
    "host_specific": True,
}

EXPECTED_SNAPSHOT = {
    "maintained_branch_ref": "main",
    "maintained_baseline": BASELINE,
    "maintained_head_observed_at_snapshot": "a4365cf673cb7995413168cb1e1439c183566268",
    "merge_base_with_preclosure_head": BASELINE,
    "maintained_unique_commit_count_at_snapshot": 4,
    "candidate_unique_commit_count_at_snapshot": 24,
    "cr2_commit_count_before_cr2_7": 12,
    "candidate_branch_retained": True,
    "candidate_worktree_retained": True,
    "merged_into_maintained_branch": False,
    "observed_remote_refs_containing_preclosure_head": [],
    "remote_observation_scope": "local_remote_tracking_refs_without_fetch",
    "source_worktree_clean_before_cr2_7": True,
    "snapshot_semantics": "observed_precommit_topology_not_permanent_ref_pin",
}

EXPECTED_MAINTAINED_BOUNDARY = {
    "cpu_backend_remains_default": True,
    "cuda_candidate_remains_unmaintained": True,
    "compiled_experimental_backend": False,
    "runtime_selector_implemented": False,
    "public_abi_promotion": False,
    "supports_device_observation_view": False,
    "supports_resident_state": False,
}

EXPECTED_ALLOWED_ACTIONS = [
    "retain_branch_worktree_commit_chain_and_evidence",
    "inspect_or_revalidate_retained_evidence_without_mutation",
    "start_a_new_explicit_program_after_user_authorization",
    "retry_achieved_counters_under_a_new_program_after_host_permission_is_available",
]

EXPECTED_FORBIDDEN_ACTIONS = [
    "runtime_facade_selection_change",
    "capability_or_support_flag_change",
    "public_abi_promotion",
    "kernel_or_launch_tuning",
    "substitute_zero_or_theoretical_values_for_blocked_counters",
    "extrapolate_unmeasured_world_counts",
    "merge_or_push",
    "change_host_profiler_permissions",
    "delete_candidate_branch_or_worktree",
]

EXPECTED_LIMITATIONS = {
    "host_specific": True,
    "background_load_uncontrolled": True,
    "balanced_power_scheme": True,
    "no_gpu_exclusive_mode": True,
    "no_process_affinity": True,
    "two_order_balanced_campaigns_only": True,
    "rollout_p95_is_maximum_of_10": True,
    "unmeasured_world_counts_unclassified": True,
    "device_consumer_cpu_comparison_unavailable": True,
    "achieved_counter_permission_blocked": True,
}

EXPECTED_RECOVERY = {
    "candidate_recovery": "retain_local_branch_worktree_and_commit_chain",
    "maintained_recovery": "no_rollback_required_cr2_did_not_mutate_maintained_ref",
    "destructive_cleanup_performed": False,
    "merge_or_push_performed_by_program": False,
    "future_deletion_requires_explicit_user_authorization": True,
}

EXPECTED_VALIDATION = {
    "validator": "tools/diagnostics/cuda_resident_cr2_closure.py",
    "architecture_guard": "tests/architecture/runtime_profiles/test_cuda_resident_cr2_closure.py",
    "closure_guard_required": True,
    "final_independent_review_required": True,
    "exact_staged_snapshot_required": True,
    "evidence_only_iteration": True,
    "runtime_regression_basis": "CR2-6b accepted validation plus CR2-7 closure guards",
}


class ClosureError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ClosureError(message)


def strict_equal(actual: object, expected: object, label: str) -> None:
    require(type(actual) is type(expected), f"{label} JSON type drifted")
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        require(set(actual) == set(expected), f"{label} keys drifted")
        for key, value in expected.items():
            strict_equal(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        require(len(actual) == len(expected), f"{label} length drifted")
        for index, value in enumerate(expected):
            strict_equal(actual[index], value, f"{label}[{index}]")
    else:
        require(actual == expected, f"{label} value drifted")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ClosureError(f"cannot load {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def _resolve(root: Path, relative: object, label: str) -> Path:
    require(type(relative) is str and bool(relative), f"{label}.path invalid")
    path = Path(str(relative).replace("docs/plan/exact_runtime/", "tests/fixtures/runtime_profiles/cuda_resident_program_2/", 1))
    require(not path.is_absolute(), f"{label}.path must be repository-relative")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()), f"{label}.path escapes repository")
    require(resolved.is_file(), f"{label}.path missing")
    return resolved


def _exact_descriptor(root: Path, value: object, label: str) -> Path:
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == {"path", "bytes", "sha256"}, f"{label} schema drifted")
    path = _resolve(root, value["path"], label)
    require(type(value["bytes"]) is int, f"{label}.bytes type drifted")
    require(value["bytes"] == path.stat().st_size, f"{label}.bytes mismatch")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(
        type(value["sha256"]) is str
        and SHA256.fullmatch(value["sha256"]) is not None
        and value["sha256"] == digest,
        f"{label}.sha256 mismatch",
    )
    return path


def _canonical_descriptor(root: Path, value: object, label: str) -> Path:
    require(isinstance(value, dict), f"{label} must be an object")
    require(
        set(value) == {"path", "canonicalization", "canonical_bytes", "sha256"},
        f"{label} schema drifted",
    )
    path = _resolve(root, value["path"], label)
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    payload = text.encode("utf-8")
    require(value["canonicalization"] == "utf8_lf", f"{label} canonicalization drifted")
    require(type(value["canonical_bytes"]) is int, f"{label}.canonical_bytes type drifted")
    require(value["canonical_bytes"] == len(payload), f"{label}.canonical_bytes mismatch")
    digest = hashlib.sha256(payload).hexdigest()
    require(
        type(value["sha256"]) is str
        and SHA256.fullmatch(value["sha256"]) is not None
        and value["sha256"] == digest,
        f"{label}.sha256 mismatch",
    )
    return path


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _validate_program(
    root: Path,
    program: object,
    *,
    check_repository: bool,
    check_live_snapshot: bool,
) -> None:
    expected = {
        "name": "cuda_resident_runtime_program_2",
        "branch": BRANCH,
        "parent_closure_commit": PARENT_CLOSURE,
        "maintained_baseline": BASELINE,
        "preclosure_head": PRE_CLOSURE_HEAD,
        "cr2_7_commit_identity": "this_commit",
        "accepted_commits_before_cr2_7": ACCEPTED_COMMITS,
    }
    strict_equal(program, expected, "program")
    chain = list(ACCEPTED_COMMITS.values())
    require(all(COMMIT.fullmatch(commit) for commit in chain), "accepted commit invalid")
    if check_repository:
        require(_git(root, "rev-parse", f"{chain[0]}^") == PARENT_CLOSURE, "CR2 parent drifted")
        for parent, child in zip(chain, chain[1:]):
            require(
                _git(root, "rev-parse", f"{child}^") == parent,
                "accepted chain is not linear",
            )
        require(
            _git(root, "merge-base", BASELINE, PRE_CLOSURE_HEAD) == BASELINE,
            "merge base drifted",
        )
        require(
            _git(root, "rev-list", "--count", f"{BASELINE}..{PRE_CLOSURE_HEAD}") == "24",
            "ahead count drifted",
        )
    if check_live_snapshot:
        require(check_repository, "live snapshot requires repository validation")
        maintained_head = EXPECTED_SNAPSHOT["maintained_head_observed_at_snapshot"]
        require(_git(root, "rev-parse", "main") == maintained_head, "maintained ref moved")
        require(
            _git(root, "merge-base", "main", PRE_CLOSURE_HEAD) == BASELINE,
            "live merge base drifted",
        )
        require(
            _git(root, "rev-list", "--left-right", "--count", f"main...{PRE_CLOSURE_HEAD}")
            == "4\t24",
            "live divergence count drifted",
        )
        require(
            _git(root, "branch", "-r", "--contains", PRE_CLOSURE_HEAD) == "",
            "remote containment drifted",
        )
        require(
            BRANCH in _git(root, "branch", "--contains", PRE_CLOSURE_HEAD),
            "candidate branch missing",
        )
        require(
            f"branch refs/heads/{BRANCH}" in _git(root, "worktree", "list", "--porcelain"),
            "candidate worktree missing",
        )


def _validate_evidence(root: Path, evidence: object) -> None:
    require(isinstance(evidence, dict), "evidence must be an object")
    require(
        set(evidence)
        == {"matrix_evidence", "parity_confirmation", "counter_evidence", "resource_evidence"},
        "evidence inventory drifted",
    )
    matrix_path = _exact_descriptor(root, evidence["matrix_evidence"], "evidence.matrix_evidence")
    parity_path = _exact_descriptor(
        root, evidence["parity_confirmation"], "evidence.parity_confirmation"
    )
    counter_path = _canonical_descriptor(
        root, evidence["counter_evidence"], "evidence.counter_evidence"
    )
    resource_path = _canonical_descriptor(
        root, evidence["resource_evidence"], "evidence.resource_evidence"
    )
    matrix = load_json(matrix_path)
    parity = load_json(parity_path)
    counter = load_json(counter_path)
    resource = load_json(resource_path)

    matrix_gates = {
        "cr2_5_achieved_counter_gate_complete": False,
        "cr2_6_matrix_evidence_complete": True,
        "cr2_6_selection_advisory_complete": True,
        "maintained_claim_allowed": False,
        "promotion_allowed": False,
        "public_support_enabled": False,
        "tuning_authorized": False,
    }
    strict_equal(matrix.get("gates"), matrix_gates, "matrix.gates")
    policy = matrix.get("selection_policy")
    require(isinstance(policy, dict), "matrix.selection_policy missing")
    strict_equal(
        policy.get("maintained_default_backend"),
        "flecs_cpu_reference",
        "matrix.selection_policy.maintained_default_backend",
    )
    strict_equal(
        policy.get("applies_only_to_measured_world_counts"),
        True,
        "matrix.selection_policy.applies_only_to_measured_world_counts",
    )
    strict_equal(
        policy.get("status"),
        "experimental_advisory_complete",
        "matrix.selection_policy.status",
    )
    parity_ref = matrix.get("parity_confirmation")
    require(isinstance(parity_ref, dict), "matrix.parity_confirmation missing")
    for field in ("path", "bytes", "sha256"):
        strict_equal(
            parity_ref.get(field),
            evidence["parity_confirmation"][field],
            f"matrix.parity_confirmation.{field}",
        )

    strict_equal(parity.get("status"), "pass", "parity.status")
    strict_equal(
        parity.get("candidate_promotion_blocked"), True, "parity.candidate_promotion_blocked"
    )
    strict_equal(parity.get("maintained_claim_allowed"), False, "parity.maintained_claim_allowed")
    strict_equal(parity.get("public_support_enabled"), False, "parity.public_support_enabled")
    coverage = parity.get("coverage")
    require(isinstance(coverage, dict), "parity.coverage missing")
    strict_equal(
        coverage.get("released_numeric_field_count"),
        12,
        "parity.coverage.released_numeric_field_count",
    )
    strict_equal(
        coverage.get("partition_complete"),
        True,
        "parity.coverage.partition_complete",
    )

    attempt = counter.get("attempt")
    require(isinstance(attempt, dict), "counter.attempt missing")
    strict_equal(attempt.get("status"), "external_blocked", "counter.attempt.status")
    strict_equal(attempt.get("blocker_code"), "ERR_NVGPUCTRPERM", "counter.attempt.blocker_code")
    strict_equal(attempt.get("collected_launch_count"), 0, "counter.attempt.collected_launch_count")
    strict_equal(attempt.get("required_launch_count"), 12, "counter.attempt.required_launch_count")
    achieved = counter.get("achieved_counters")
    require(isinstance(achieved, dict) and len(achieved) == 5, "counter achieved families drifted")
    for family, payload in achieved.items():
        require(isinstance(payload, dict), f"counter.{family} invalid")
        for field in ("metric_names", "provenance", "values_by_launch"):
            strict_equal(payload.get(field), None, f"counter.{family}.{field}")
    counter_gates = counter.get("gates")
    resource_gates = resource.get("gates")
    require(isinstance(counter_gates, dict), "counter.gates missing")
    require(isinstance(resource_gates, dict), "resource.gates missing")
    strict_equal(
        counter_gates.get("cr2_5_achieved_counter_gate_complete"),
        False,
        "counter achieved gate",
    )
    strict_equal(counter_gates.get("tuning_authorized"), False, "counter tuning gate")
    strict_equal(
        resource_gates.get("cr2_5a_static_resource_complete"),
        True,
        "resource static gate",
    )
    strict_equal(
        resource_gates.get("cr2_5a_launch_topology_complete"),
        True,
        "resource topology gate",
    )


def _validate_runtime_boundary(root: Path, *, check_repository: bool) -> None:
    config = (root / "src/runtime/facade/runtime_facade_config.cpp").read_text(encoding="utf-8")
    for fragment in (
        ".compiled_experimental_backend = false",
        ".supports_device_observation_view = false",
        ".supports_resident_state = false",
    ):
        require(fragment in config, f"maintained boundary drifted: {fragment}")
    if not check_repository:
        return
    paths = [
        "CMakeLists.txt",
        "cmake",
        "src/runtime/contracts",
        "src/runtime/facade",
        "src/tools/experimental/cuda_resident",
        "src/tests",
    ]
    completed = subprocess.run(
        ["git", "diff", "--quiet", PRE_CLOSURE_HEAD, CLOSURE_COMMIT, "--", *paths],
        cwd=root,
        check=False,
    )
    require(completed.returncode == 0, "CR2-7 must not modify runtime, probe, build, or C++ tests")


def validate_record(
    root: Path,
    record: dict[str, Any],
    *,
    check_repository: bool = True,
    check_live_snapshot: bool = False,
) -> None:
    expected_keys = {
        "schema_version",
        "closure_id",
        "date",
        "authority",
        "status",
        "program",
        "decision",
        "gate_evaluation",
        "evidence",
        "selection_advisory_summary",
        "repository_snapshot",
        "maintained_runtime_boundary",
        "allowed_future_actions",
        "forbidden_under_closed_program",
        "limitations",
        "rollback_and_recovery",
        "validation",
    }
    require(set(record) == expected_keys, "closure top-level schema drifted")
    strict_equal(record["schema_version"], SCHEMA, "schema_version")
    strict_equal(record["closure_id"], CLOSURE_ID, "closure_id")
    strict_equal(record["date"], "2026-08-05", "date")
    strict_equal(record["authority"], "cuda_resident_runtime_program_2", "authority")
    strict_equal(record["status"], "closed_without_promotion", "status")
    _validate_program(
        root,
        record["program"],
        check_repository=check_repository,
        check_live_snapshot=check_live_snapshot,
    )
    strict_equal(record["decision"], EXPECTED_DECISION, "decision")
    strict_equal(record["gate_evaluation"], EXPECTED_GATES, "gate_evaluation")
    _validate_evidence(root, record["evidence"])
    strict_equal(record["selection_advisory_summary"], EXPECTED_SELECTION, "selection")
    strict_equal(record["repository_snapshot"], EXPECTED_SNAPSHOT, "repository_snapshot")
    strict_equal(
        record["maintained_runtime_boundary"],
        EXPECTED_MAINTAINED_BOUNDARY,
        "maintained_runtime_boundary",
    )
    strict_equal(
        record["allowed_future_actions"], EXPECTED_ALLOWED_ACTIONS, "allowed_future_actions"
    )
    strict_equal(
        record["forbidden_under_closed_program"],
        EXPECTED_FORBIDDEN_ACTIONS,
        "forbidden_under_closed_program",
    )
    strict_equal(record["limitations"], EXPECTED_LIMITATIONS, "limitations")
    strict_equal(record["rollback_and_recovery"], EXPECTED_RECOVERY, "rollback_and_recovery")
    strict_equal(record["validation"], EXPECTED_VALIDATION, "validation")
    _validate_runtime_boundary(root, check_repository=check_repository)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the CR2-7 no-promotion closure")
    parser.add_argument(
        "--record",
        type=Path,
        default=Path("tests/fixtures/runtime_profiles/cuda_resident_program_2/cuda_resident_cr2_closure_20260805.json"),
    )
    parser.add_argument("--check-live-snapshot", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    record_path = args.record if args.record.is_absolute() else root / args.record
    validate_record(root, load_json(record_path), check_live_snapshot=args.check_live_snapshot)
    print(f"{CLOSURE_ID}: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
