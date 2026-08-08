from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLOSURE_PATH = ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb11_closure_20260731.json"
EVIDENCE = ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb9_evidence_20260730"
BASELINE = "395e02b7dfeaa87baedb2611ec503d14ab137ce3"
RB10_COMMIT = "e5ea624fc1688d6e9d8b00ae64670ddcc2e3bd02"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_rb11_closure_is_bound_to_rb10_and_the_retained_evidence() -> None:
    closure = _json(CLOSURE_PATH)
    rb10 = _json(
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb10_hold_decision_20260731.json"
    )
    retained = closure["retained_artifacts"]
    assert isinstance(retained, dict)
    rb10_ref = retained["rb10_decision"]
    rb9_ref = retained["rb9_comparison"]
    assert isinstance(rb10_ref, dict)
    assert isinstance(rb9_ref, dict)

    assert closure["schema_version"] == "cuda_resident.program_closure.v1"
    assert closure["closure_id"] == "rb11.closed_without_promotion.cuda_resident.20260731"
    assert closure["decision"]["closure_disposition"] == "closed_without_promotion"
    assert closure["decision"]["promotion_allowed"] is False
    assert closure["decision"]["runtime_mutation_allowed"] is False
    assert rb10["status"] == "hold"
    assert rb10_ref["sha256"] == _sha256(
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb10_hold_decision_20260731.json"
    )
    assert rb9_ref["sha256"] == _sha256(EVIDENCE / "comparison.json")
    assert retained["rb9_cpu_lane_sha256"] == _sha256(EVIDENCE / "cpu_lane.json")
    assert retained["rb9_cuda_lane_sha256"] == _sha256(EVIDENCE / "cuda_lane.json")


def test_rb11_closure_preserves_baseline_branch_and_maintained_flags() -> None:
    closure = _json(CLOSURE_PATH)
    program = closure["program"]
    snapshot = closure["repository_snapshot"]
    boundary = closure["maintained_runtime_boundary"]
    recovery = closure["rollback_and_recovery"]
    assert isinstance(program, dict)
    assert isinstance(snapshot, dict)
    assert isinstance(boundary, dict)
    assert isinstance(recovery, dict)

    commits = program["accepted_commits_before_rb11"]
    assert isinstance(commits, dict)
    assert set(commits) == {f"RB{i}" for i in range(11)}
    assert all(isinstance(value, str) and HEX40.fullmatch(value) for value in commits.values())
    assert program["baseline_commit"] == BASELINE
    assert program["preclosure_head"] == RB10_COMMIT
    assert program["branch"] == "codex/cuda-resident-backend"
    assert program["rb11_commit_identity"] == "this_commit"

    assert snapshot == {
        "candidate_ahead_count_before_rb11": 11,
        "candidate_branch_retained": True,
        "candidate_worktree_retained": True,
        "maintained_ahead_count": 0,
        "maintained_branch": "main",
        "maintained_head": BASELINE,
        "merge_base": BASELINE,
        "merged_into_maintained_branch": False,
        "observed_remote_refs_containing_preclosure_head": [],
        "remote_observation_scope": "local_remote_tracking_refs_without_fetch",
    }
    assert boundary == {
        "compiled_experimental_backend": False,
        "cpu_backend_remains_default": True,
        "public_abi_promotion": False,
        "supports_device_observation_view": False,
        "supports_resident_state": False,
    }
    assert recovery == {
        "candidate_recovery": "retain_local_branch_worktree_and_commit_chain",
        "destructive_cleanup_performed": False,
        "future_deletion_requires_explicit_user_authorization": True,
        "maintained_recovery": "no_rollback_required_main_remains_at_baseline",
        "merge_or_push_performed_by_program": False,
    }


def test_rb11_git_snapshot_is_reconstructible_from_frozen_commits() -> None:
    assert _git("rev-parse", BASELINE) == BASELINE
    assert _git("rev-parse", RB10_COMMIT) == RB10_COMMIT
    assert _git("merge-base", BASELINE, RB10_COMMIT) == BASELINE
    assert _git("rev-list", "--count", f"{BASELINE}..{RB10_COMMIT}") == "11"
    assert (
        _git("rev-list", "--left-right", "--count", f"{BASELINE}...{RB10_COMMIT}")
        == "0\t11"
    )
    assert _git("rev-list", "--merges", f"{BASELINE}..{RB10_COMMIT}") == ""
    assert _git("merge-base", "--is-ancestor", RB10_COMMIT, "HEAD") == ""


def test_rb11_closure_has_bilingual_links_and_byte_stable_json_guards() -> None:
    closure = _json(CLOSURE_PATH)
    assert CLOSURE_PATH.stat().st_size < 12_000
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "cuda_resident_rb10_hold_decision_20260731.json -text" in attributes
    assert "cuda_resident_rb11_closure_20260731.json -text" in attributes

    english = (
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb11_closure_20260731.md"
    ).read_text(encoding="utf-8")
    chinese = (
        ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/cuda_resident_rb11_closure_20260731.zh.md"
    ).read_text(encoding="utf-8")
    english_index = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/README.md").read_text(encoding="utf-8")
    chinese_index = (ROOT / "docs/plan/archive/exact_runtime/completed_programs_20260729_20260805/README.zh.md").read_text(encoding="utf-8")
    parent_english = (ROOT / "docs/plan/archive/owner_migration_20260808/README.md").read_text(encoding="utf-8")
    parent_chinese = (ROOT / "docs/plan/archive/owner_migration_20260808/README.zh.md").read_text(encoding="utf-8")
    for text in (english, chinese):
        assert "rb11.closed_without_promotion.cuda_resident.20260731" in text
        assert "cuda_resident_rb11_closure_20260731.json" in text
        assert "e5ea624fc1688d6e9d8b00ae64670ddcc2e3bd02" in text
    assert "cuda_resident_rb11_closure_20260731.md" in english_index
    assert "cuda_resident_rb11_closure_20260731.zh.md" in chinese_index
    assert "RB0-RB11 closed without promotion" in parent_english
    assert "RB0-RB11 无晋级关闭" in parent_chinese
    assert closure["validation"]["final_independent_review_required"] is True
