from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import cuda_resident_cr2_closure as closure_validator


ROOT = Path(__file__).resolve().parents[3]
CLOSURE = ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_cr2_closure_20260805.json"
PRE_CLOSURE_HEAD = "356bcd56a61e40f1327d16b6a2dda335d7fdd553"
CLOSURE_COMMIT = closure_validator.CLOSURE_COMMIT


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_descriptor(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    payload = text.encode("utf-8")
    return {
        "path": path.relative_to(ROOT).as_posix().replace("docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/", "docs/plan/exact_runtime/", 1),
        "canonicalization": "utf8_lf",
        "canonical_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_cr2_7_tracked_closure_and_historical_snapshot_are_strict() -> None:
    record = closure_validator.load_json(CLOSURE)
    closure_validator.validate_record(ROOT, record, check_live_snapshot=False)
    assert record["schema_version"] == closure_validator.SCHEMA
    assert record["closure_id"] == closure_validator.CLOSURE_ID
    assert record["status"] == "closed_without_promotion"
    snapshot = record["repository_snapshot"]
    assert snapshot["maintained_head_observed_at_snapshot"] == (
        "a4365cf673cb7995413168cb1e1439c183566268"
    )
    assert snapshot["maintained_unique_commit_count_at_snapshot"] == 4
    assert snapshot["candidate_unique_commit_count_at_snapshot"] == 24
    assert snapshot["snapshot_semantics"] == "observed_precommit_topology_not_permanent_ref_pin"
    assert CLOSURE.stat().st_size < 32_768


def test_cr2_7_is_bound_to_exact_and_canonical_evidence() -> None:
    record = _load(CLOSURE)
    evidence = record["evidence"]
    assert isinstance(evidence, dict)
    for name in ("matrix_evidence", "parity_confirmation"):
        descriptor = evidence[name]
        assert isinstance(descriptor, dict)
        path = ROOT / str(descriptor["path"]).replace("docs/plan/exact_runtime/", "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/", 1)
        assert descriptor == {
            "path": path.relative_to(ROOT).as_posix().replace("docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/", "docs/plan/exact_runtime/", 1),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    for name in ("counter_evidence", "resource_evidence"):
        descriptor = evidence[name]
        assert isinstance(descriptor, dict)
        path = ROOT / str(descriptor["path"]).replace("docs/plan/exact_runtime/", "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/", 1)
        assert descriptor == _canonical_descriptor(path)


def test_cr2_7_records_the_complete_linear_program_chain() -> None:
    record = _load(CLOSURE)
    program = record["program"]
    assert isinstance(program, dict)
    commits = program["accepted_commits_before_cr2_7"]
    assert commits == closure_validator.ACCEPTED_COMMITS
    chain = list(commits.values())
    assert _git("rev-parse", f"{chain[0]}^") == closure_validator.PARENT_CLOSURE
    for parent, child in zip(chain, chain[1:]):
        assert _git("rev-parse", f"{child}^") == parent
    assert chain[-1] == PRE_CLOSURE_HEAD
    assert _git("merge-base", closure_validator.BASELINE, PRE_CLOSURE_HEAD) == (
        closure_validator.BASELINE
    )
    assert _git("rev-list", "--count", f"{closure_validator.BASELINE}..{PRE_CLOSURE_HEAD}") == (
        "24"
    )


def test_cr2_7_closes_failed_gates_without_relabeling_the_advisory() -> None:
    record = _load(CLOSURE)
    gates = record["gate_evaluation"]
    decision = record["decision"]
    selection = record["selection_advisory_summary"]
    assert gates == closure_validator.EXPECTED_GATES
    assert decision == closure_validator.EXPECTED_DECISION
    assert selection == closure_validator.EXPECTED_SELECTION
    assert gates["achieved_counter_gate_complete"] is False
    assert gates["promotion_prerequisites_complete"] is False
    assert decision["promotion_authorization_recorded"] is False
    assert decision["integration_plan_authorized"] is False
    assert decision["promotion_allowed"] is False
    assert decision["runtime_selection_allowed"] is False
    assert decision["tuning_allowed"] is False
    assert selection["maintained_default_backend"] == "flecs_cpu_reference"
    assert selection["unmeasured_world_counts"] == "unclassified_no_extrapolation"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"status": False}),
        lambda value: value["decision"].update({"promotion_allowed": True}),
        lambda value: value["decision"].update({"promotion_authorization_recorded": 0}),
        lambda value: value["gate_evaluation"].update({"achieved_counter_gate_complete": True}),
        lambda value: value["gate_evaluation"]["blocking_conditions"].pop(0),
        lambda value: value["selection_advisory_summary"].update(
            {"maintained_default_backend": "cuda_resident"}
        ),
        lambda value: value["selection_advisory_summary"].update({"host_specific": 1}),
        lambda value: value["repository_snapshot"].update(
            {"candidate_unique_commit_count_at_snapshot": True}
        ),
        lambda value: value["maintained_runtime_boundary"].update(
            {"compiled_experimental_backend": True}
        ),
        lambda value: value["allowed_future_actions"].append("silently_promote"),
        lambda value: value["limitations"].update({"host_specific": False}),
        lambda value: value["validation"].update({"final_independent_review_required": 1}),
        lambda value: value["evidence"]["matrix_evidence"].update({"bytes": True}),
    ],
)
def test_cr2_7_validator_rejects_gate_type_scope_or_evidence_drift(mutation) -> None:
    record = deepcopy(_load(CLOSURE))
    mutation(record)
    with pytest.raises(closure_validator.ClosureError):
        closure_validator.validate_record(
            ROOT,
            record,
            check_repository=False,
            check_live_snapshot=False,
        )


def test_cr2_7_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"status":"closed","status":"promoted"}', encoding="utf-8")
    with pytest.raises(closure_validator.ClosureError, match="duplicate JSON key"):
        closure_validator.load_json(path)


def test_cr2_7_is_evidence_only_and_preserves_the_maintained_boundary() -> None:
    record = _load(CLOSURE)
    assert record["maintained_runtime_boundary"] == (closure_validator.EXPECTED_MAINTAINED_BOUNDARY)
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            PRE_CLOSURE_HEAD,
            CLOSURE_COMMIT,
            "--",
            "CMakeLists.txt",
            "cmake",
            "src/runtime/contracts",
            "src/runtime/facade",
            "src/tools/experimental/cuda_resident",
            "src/tests",
        ],
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0


def test_cr2_7_has_bilingual_terminal_links_and_byte_stable_record() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "cuda_resident_cr2_closure_20260805.json -text" in attributes
    english = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_cr2_closure_20260805.md").read_text(
        encoding="utf-8"
    )
    chinese = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_cr2_closure_20260805.zh.md").read_text(
        encoding="utf-8"
    )
    for text in (english, chinese):
        assert closure_validator.CLOSURE_ID in text
        assert "cuda_resident_cr2_closure_20260805.json" in text
        assert PRE_CLOSURE_HEAD in text
    exact_index = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/README.md").read_text(encoding="utf-8")
    exact_index_zh = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/README.zh.md").read_text(encoding="utf-8")
    parent = (ROOT / "docs/plan/archive/owner_migration_20260808/README.md").read_text(encoding="utf-8")
    parent_zh = (ROOT / "docs/plan/archive/owner_migration_20260808/README.zh.md").read_text(encoding="utf-8")
    program = (
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_runtime_program_2_20260731.md"
    ).read_text(encoding="utf-8")
    program_zh = (
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_runtime_program_2_20260731.zh.md"
    ).read_text(encoding="utf-8")
    assert "cuda_resident_cr2_closure_20260805.md" in exact_index
    assert "cuda_resident_cr2_closure_20260805.zh.md" in exact_index_zh
    assert "CR2-0 through CR2-7 closed without promotion" in parent
    assert "CR2-0 至 CR2-7 无晋级关闭" in parent_zh
    assert "closed without promotion" in program
    assert "无晋级关闭" in program_zh


def test_cr2_7_new_modules_and_artifacts_remain_bounded() -> None:
    validator = ROOT / "tools/diagnostics/cuda_resident_cr2_closure.py"
    test = Path(__file__)
    assert len(validator.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(test.read_text(encoding="utf-8").splitlines()) <= 700
    for path in (
        CLOSURE,
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_cr2_closure_20260805.md",
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_cr2_closure_20260805.zh.md",
    ):
        assert path.stat().st_size < 524_288
