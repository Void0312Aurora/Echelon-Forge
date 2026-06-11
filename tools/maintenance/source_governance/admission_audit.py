#!/usr/bin/env python3
"""Read-only admission audit for A2 high-fidelity damage source docs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ARCHIVED_A2_ROOT = Path("docs/task/air_combat/archive/a2_high_fidelity_damage_model")
LEGACY_A2_ROOT = Path("docs/task/air_combat/a2_high_fidelity_damage_model")

SOURCE_LEDGER_GLOB = "*/source_ledger*.zh.md"
CALIBRATION_MARKDOWN_GLOB = "*/*.zh.md"
CANDIDATE_UPDATE_GLOBS = (
    "**/*update*.zh.md",
    "**/*source_pin_integration*.zh.md",
)

LEDGER_REQUIRED_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("source-ref", ("source_ref", "URL", "DOI", "报告号", "标准号")),
    ("publisher-holder", ("发布方", "持有人", "publisher", "holder")),
    ("rights", ("权利", "可公开", "public", "license", "版权", "再分发")),
    ("scope", ("scope", "范围", "匹配")),
    ("cross-validation", ("交叉验证", "cross", "互证")),
    ("residual", ("residual", "不确定", "风险", "缺口")),
    ("authority-boundary", ("non-authoritative", "不授予", "authority=`none`", "authority 状态")),
)

RUNTIME_AUTHORITY_FIELDS = (
    "effect_scale_authority",
    "component_failure_probability_authority",
    "pk_authority",
    "deterministic_fuze_authority",
)

STATUS_FIELD_NAMES = (
    "validation_status",
    "calibration_status",
)

AUTHORITY_TRUE_RE = re.compile(
    r"(?:^|\|)\s*`?(?P<field>"
    + "|".join(re.escape(field) for field in RUNTIME_AUTHORITY_FIELDS)
    + r")`?\s*\|\s*`?(?P<value>true|yes|passed|validated|calibrated)`?",
    re.IGNORECASE,
)
STATUS_PASSED_RE = re.compile(
    r"(?:^|\|)\s*`?(?P<field>validation_status|calibration_status)`?\s*\|\s*`?(?P<value>passed|validated|calibrated)`?",
    re.IGNORECASE,
)
DESCRIPTOR_CREATION_RE = re.compile(
    r"(创建|create|created).{0,32}(runtime descriptor|vulnerability descriptor|authoritative descriptor)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class AuditSummary:
    checked_ledgers: int
    checked_candidate_docs: int
    checked_calibration_docs: int
    issues: list[Issue]


def rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells)


def looks_like_source_row(cells: list[str]) -> bool:
    if len(cells) < 7 or is_separator_row(cells):
        return False
    first_two = " ".join(cells[:2])
    return bool(
        re.search(
            r"(SRC|A2|CFBM|GMD|GEB|MECH|VPS|F16|AIM120|REJ|TODO|RES)-",
            first_two,
            re.IGNORECASE,
        )
    )


def row_mentions_stable_ref(row_text: str) -> bool:
    return bool(
        re.search(
            r"https?://|doi\.org|DOI|ISBN|NTRS|NTIS|DTIC|DLA|ASSIST|"
            r"report|报告|标准|题录|Technical Paper|TP-\d+|ARBRL-TR|"
            r"BRL Report|MIL-HDBK|MIL-STD|TM\s+\d|category[_ -]record|"
            r"rejection[_ -]category|search[_ -]lead|examples/",
            row_text,
            re.IGNORECASE,
        )
    )


def row_mentions_non_authority(row_text: str) -> bool:
    lowered = row_text.lower()
    return (
        "non-authoritative" in lowered
        or "candidate" in lowered
        or "authority=`none`" in lowered
        or "authority=none" in lowered
        or "authority none" in lowered
        or "authority: none" in lowered
        or "no authority" in lowered
        or "no authoritative" in lowered
        or "not authoritative" in lowered
        or "not descriptor" in lowered
        or "sanity" in lowered
        or "residual_reference" in lowered
        or "background_only" in lowered
        or "不授予" in row_text
        or "不得" in row_text
        or "不可" in row_text
        or "不能" in row_text
        or "不是" in row_text
        or "不含" in row_text
        or "不包含" in row_text
        or "不提供" in row_text
        or "不采纳" in row_text
        or "不作为" in row_text
        or "只记录" in row_text
        or "候选" in row_text
        or "rejected" in lowered
        or "pending" in lowered
    )


def append_issue(
    issues: list[Issue],
    severity: str,
    code: str,
    path: Path,
    repo_root: Path,
    message: str,
) -> None:
    issues.append(Issue(severity=severity, code=code, path=rel(path, repo_root), message=message))


def audit_source_ledger(path: Path, repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)

    for concept_id, needles in LEDGER_REQUIRED_CONCEPTS:
        if not any(needle.lower() in text.lower() for needle in needles):
            append_issue(
                issues,
                "error",
                f"ledger-missing-{concept_id}",
                path,
                repo_root,
                f"source ledger does not mention required admission concept: {concept_id}",
            )

    rows = [cells for line in text.splitlines() if (cells := table_cells(line))]
    source_rows = [cells for cells in rows if looks_like_source_row(cells)]
    if not source_rows:
        append_issue(
            issues,
            "error",
            "ledger-no-source-rows",
            path,
            repo_root,
            "source ledger has no recognizable source/rejection rows",
        )
        return issues

    for index, cells in enumerate(source_rows, start=1):
        row_text = " | ".join(cells)
        if not row_mentions_stable_ref(row_text):
            append_issue(
                issues,
                "warning",
                "ledger-row-unstable-source-ref",
                path,
                repo_root,
                f"row {index} does not expose an obvious stable source_ref, DOI, URL, report, or catalog handle",
            )
        if not row_mentions_non_authority(row_text):
            append_issue(
                issues,
                "warning",
                "ledger-row-missing-authority-boundary",
                path,
                repo_root,
                f"row {index} does not explicitly state candidate/non-authoritative/rejected/pending boundary",
            )

    return issues


def audit_calibration_doc(path: Path, repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)

    if "non-authoritative" not in text.lower() and "不授予" not in text:
        append_issue(
            issues,
            "error",
            "calibration-doc-missing-non-authority",
            path,
            repo_root,
            "calibration candidate doc must retain an explicit non-authoritative boundary",
        )

    for line_no, line in enumerate(text.splitlines(), start=1):
        if match := AUTHORITY_TRUE_RE.search(line):
            append_issue(
                issues,
                "error",
                "calibration-doc-authority-true",
                path,
                repo_root,
                f"line {line_no} sets {match.group('field')} to {match.group('value')}",
            )
        if match := STATUS_PASSED_RE.search(line):
            append_issue(
                issues,
                "error",
                "calibration-doc-status-passed",
                path,
                repo_root,
                f"line {line_no} sets {match.group('field')} to {match.group('value')}",
            )

    lowered = text.lower()
    claims_descriptor = DESCRIPTOR_CREATION_RE.search(text)
    has_negative_descriptor_boundary = any(
        phrase in lowered
        for phrase in (
            "not_created",
            "not created",
            "must not create",
            "cannot create",
            "不创建",
            "不能创建",
            "不得创建",
            "不得据此创建",
        )
    )
    if claims_descriptor and not has_negative_descriptor_boundary:
        append_issue(
            issues,
            "error",
            "calibration-doc-claims-descriptor",
            path,
            repo_root,
            "candidate calibration doc appears to claim descriptor creation without a negative boundary",
        )

    if path.name.startswith("validation_manifest") or path.name.startswith("validation_report"):
        if "validation_status" not in text:
            append_issue(
                issues,
                "error",
                "calibration-doc-missing-validation-status",
                path,
                repo_root,
                "validation candidate doc must name validation_status",
            )
        if "validation_artifact_sha256" not in text and "sha256" not in lowered:
            append_issue(
                issues,
                "error",
                "calibration-doc-missing-artifact-sha256",
                path,
                repo_root,
                "validation candidate doc must track artifact sha256/checksum status",
            )

    return issues


def audit_candidate_update_doc(path: Path, repo_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    lowered = text.lower()
    third_party_label_markers = (
        "third_party_candidate",
        "community_sanity_check",
        "open_source_config_candidate",
        "non-authoritative_estimate",
        "third-party candidate",
        "community sanity",
        "open-source config",
        "第三方候选",
        "社区 sanity",
        "开源配置候选",
        "非权威估计",
    )
    is_third_party_update = "third_party_community" in path.name.lower() or any(
        marker in lowered
        for marker in third_party_label_markers
    )

    if not any(
        marker in lowered or marker in text
        for marker in (
            "non-authoritative",
            "authority=`none`",
            "not_admitted",
            "rejected",
            "pending",
            "非权威",
            "不授予",
            "不得",
            "不能",
            "候选",
            "拒绝",
            "待",
        )
    ):
        append_issue(
            issues,
            "error",
            "candidate-doc-missing-non-authority",
            path,
            repo_root,
            "candidate source update must retain an explicit non-authoritative or pending/rejected boundary",
        )

    if not any(
        marker in lowered or marker in text
        for marker in ("source_ref", "url", "doi", "ntrs", "ntis", "报告", "标准", "来源")
    ):
        append_issue(
            issues,
            "warning",
            "candidate-doc-missing-source-ref-surface",
            path,
            repo_root,
            "candidate source update does not expose an obvious source_ref, URL, DOI, report, or catalog surface",
        )

    if is_third_party_update and not any(
        marker in lowered or marker in text
        for marker in third_party_label_markers
    ):
        append_issue(
            issues,
            "error",
            "candidate-doc-missing-third-party-label",
            path,
            repo_root,
            "third-party/community source updates must label the source nature",
        )

    if is_third_party_update and not any(
        marker in lowered or marker in text
        for marker in (
            "reasonableness",
            "reasonable",
            "合理性",
            "量级",
            "单位",
            "cross",
            "交叉验证",
            "residual",
            "缺口",
        )
    ):
        append_issue(
            issues,
            "error",
            "candidate-doc-missing-third-party-reasonableness",
            path,
            repo_root,
            "third-party/community source updates must include reasonableness, cross-check, or residual assessment",
        )

    for line_no, line in enumerate(text.splitlines(), start=1):
        if match := AUTHORITY_TRUE_RE.search(line):
            append_issue(
                issues,
                "error",
                "candidate-doc-authority-true",
                path,
                repo_root,
                f"line {line_no} sets {match.group('field')} to {match.group('value')}",
            )
        if match := STATUS_PASSED_RE.search(line):
            append_issue(
                issues,
                "error",
                "candidate-doc-status-passed",
                path,
                repo_root,
                f"line {line_no} sets {match.group('field')} to {match.group('value')}",
            )

    return issues


def collect_candidate_update_docs(a2_root: Path) -> list[Path]:
    paths: set[Path] = set()
    if not a2_root.exists():
        return []
    for pattern in CANDIDATE_UPDATE_GLOBS:
        paths.update(a2_root.glob(pattern))
    return sorted(
        path
        for path in paths
        if path.is_file() and path.suffix == ".md"
    )


def resolve_a2_root(repo_root: Path) -> Path:
    archived = repo_root / ARCHIVED_A2_ROOT
    legacy = repo_root / LEGACY_A2_ROOT
    if archived.exists() and (
        (archived / "data_collection").exists()
        or (archived / "calibration").exists()
    ):
        return ARCHIVED_A2_ROOT
    return LEGACY_A2_ROOT


def audit_a2_source_admission(repo_root: Path = REPO_ROOT) -> AuditSummary:
    repo_root = repo_root.resolve()
    a2_root_rel = resolve_a2_root(repo_root)
    a2_root = repo_root / a2_root_rel
    data_collection = a2_root / "data_collection"
    calibration = a2_root / "calibration"
    issues: list[Issue] = []

    ledger_paths = sorted(data_collection.glob(SOURCE_LEDGER_GLOB)) if data_collection.exists() else []
    candidate_update_paths = collect_candidate_update_docs(a2_root)
    calibration_paths = sorted(calibration.glob(CALIBRATION_MARKDOWN_GLOB)) if calibration.exists() else []

    if data_collection.exists() and not ledger_paths:
        issues.append(
            Issue(
                severity="error",
                code="no-source-ledgers",
                path=rel(data_collection, repo_root),
                message="data_collection exists but no source ledger docs were found",
            )
        )

    for path in ledger_paths:
        issues.extend(audit_source_ledger(path, repo_root))

    for path in candidate_update_paths:
        issues.extend(audit_candidate_update_doc(path, repo_root))

    for path in calibration_paths:
        issues.extend(audit_calibration_doc(path, repo_root))

    return AuditSummary(
        checked_ledgers=len(ledger_paths),
        checked_candidate_docs=len(candidate_update_paths),
        checked_calibration_docs=len(calibration_paths),
        issues=issues,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit A2 damage-model public-source admission docs.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures. Errors always fail.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = audit_a2_source_admission(Path(args.repo_root))

    if args.json:
        print(json.dumps(asdict(summary), ensure_ascii=False, indent=2))
    else:
        print(
            "A2 source admission audit: "
            f"{summary.checked_ledgers} ledgers, "
            f"{summary.checked_candidate_docs} candidate docs, "
            f"{summary.checked_calibration_docs} calibration docs"
        )
        for issue in summary.issues:
            print(f"{issue.severity.upper()} {issue.code} {issue.path}: {issue.message}")

    has_errors = any(issue.severity == "error" for issue in summary.issues)
    has_warnings = any(issue.severity == "warning" for issue in summary.issues)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
