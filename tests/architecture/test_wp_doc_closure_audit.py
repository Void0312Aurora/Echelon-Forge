from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import wp_doc_closure_audit as audit


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_wp_doc_closure_audit_accepts_current_wp9_package() -> None:
    result = audit.audit_wp(audit.REPO_ROOT, "WP9")

    assert result.folder == "docs/task/simulation_architecture/wp9_contract_infrastructure_closure"
    assert result.acceptance_reviews
    assert not [issue for issue in result.issues if issue.severity == "error"]


def test_wp_doc_closure_audit_reports_required_peer_and_index_gaps(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/task/simulation_architecture/README.md",
        "# Simulation Architecture\n\nWP10\n",
    )
    _write(
        tmp_path / "docs/task/simulation_architecture/README.zh.md",
        "# 仿真架构\n\nWP10\n",
    )
    _write(
        tmp_path
        / "docs/task/simulation_architecture/wp10_example/example_wp10_20260520.md",
        "# WP10 Example\n\n[missing](missing.md)\n",
    )
    _write(
        tmp_path / "docs/task/review/README.md",
        "# Review\n",
    )
    _write(
        tmp_path / "docs/task/review/README.zh.md",
        "# 审查\n",
    )
    _write(
        tmp_path / "docs/task/review/wp10_example_acceptance_review_20260520.md",
        "# WP10 Example Acceptance\n",
    )

    result = audit.audit_wp(tmp_path, "WP10")
    codes = {issue.code for issue in result.issues}

    assert "missing-required-zh-peer" in codes
    assert "missing-acceptance-zh-peer" in codes
    assert "review-index-missing-acceptance" in codes
    assert "broken-markdown-link" in codes


def test_wp_doc_closure_audit_normalizes_decimal_wp_labels() -> None:
    assert audit.normalize_wp_key("WP2.5") == "wp25"
    assert audit.normalize_wp_key("wp7_5") == "wp75"
    assert audit.display_wp("wp25") == "WP2.5"
    assert audit.display_wp("wp9") == "WP9"
