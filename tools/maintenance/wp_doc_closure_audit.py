#!/usr/bin/env python3
"""Audit simulation-architecture WP closure docs without rewriting them.

The tool is intentionally read-only. It produces a handoff checklist and a
generated closure summary for documentation workers instead of making the main
implementation path manually synchronize README, review, archive, and bilingual
links.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_ARCH_DIR = Path("docs/task/simulation_architecture")
REVIEW_DIR = Path("docs/task/review")
WP_DECIMAL_LABELS = {
    "wp25": "WP2.5",
    "wp75": "WP7.5",
}
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STATUS_LINE_RE = re.compile(r"^Status:\s*(.*)$")


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str
    owner: str = "closure_subagent"


@dataclass(frozen=True)
class WpAudit:
    wp: str
    wp_key: str
    folder: str | None
    task_docs: list[str]
    acceptance_reviews: list[str]
    issues: list[Issue]


@dataclass(frozen=True)
class MentionStatus:
    path: str
    applicable: bool
    mentioned: bool
    note: str


@dataclass(frozen=True)
class PeerStatus:
    required_total: int
    required_present: int
    required_missing: int
    all_present: bool
    missing_paths: list[str]


@dataclass(frozen=True)
class WpClosureSummary:
    wp: str
    wp_key: str
    folder: str | None
    primary_task_doc: str | None
    task_status: str | None
    planned_stage: bool
    task_docs_count: int
    canonical_task_docs_count: int
    acceptance_reviews_count: int
    missing_acceptance_review_expected: bool
    required_zh_peer_status: PeerStatus
    readme_index_mentions: list[MentionStatus]
    checklist: list[str]
    authority_boundary: str
    canonical_authority: str


def normalize_wp_key(value: str) -> str:
    raw = value.strip().lower().replace(" ", "")
    match = re.search(r"wp[-_]?([0-9]+(?:[._][0-9]+)?)", raw)
    if match:
        digits = match.group(1)
    else:
        digits = raw.removeprefix("wp")
    digits = digits.replace(".", "").replace("_", "")
    if not digits.isdigit():
        raise ValueError(f"cannot parse work package label: {value!r}")
    return f"wp{digits}"


def display_wp(wp_key: str) -> str:
    return WP_DECIMAL_LABELS.get(wp_key, f"WP{wp_key.removeprefix('wp')}")


def rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def required_peer_kind(path: Path) -> str | None:
    """Return required/optional peer status for a canonical markdown file."""

    if path.name.endswith(".zh.md") or not path.name.endswith(".md"):
        return None
    lower = path.name.lower()
    if lower == "readme.md":
        return "required"
    if "evidence" in lower or "notes" in lower:
        return "optional"
    if "acceptance_review" in lower:
        return "required"
    if "_cluster_" in lower or lower.endswith("_cluster.md"):
        return "required"
    if re.search(r"wp[0-9]+", lower):
        return "required"
    return None


def zh_peer(path: Path) -> Path:
    if path.name.endswith(".zh.md"):
        return path
    return path.with_name(f"{path.stem}.zh.md")


def discover_wp_folders(repo_root: Path) -> dict[str, Path]:
    sim_dir = repo_root / SIM_ARCH_DIR
    out: dict[str, Path] = {}
    if not sim_dir.exists():
        return out
    search_roots = (sim_dir, sim_dir / "archive")
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in sorted(search_root.iterdir()):
            if not path.is_dir() or not path.name.startswith("wp"):
                continue
            try:
                wp_key = normalize_wp_key(path.name)
            except ValueError:
                continue
            out.setdefault(wp_key, path)
    return out


def find_acceptance_reviews(repo_root: Path, wp_key: str) -> list[Path]:
    review_dir = repo_root / REVIEW_DIR
    candidates = [
        *review_dir.glob(f"{wp_key}_*acceptance_review_*.md"),
        *review_dir.glob(f"archive/wp-acceptance/{wp_key}_*acceptance_review_*.md"),
    ]
    return sorted(p for p in candidates if p.is_file())


def _strip_fragment_and_query(target: str) -> str:
    target = target.strip().strip("<>")
    target = target.split("#", 1)[0]
    target = target.split("?", 1)[0]
    return unquote(target.strip())


def is_external_or_anchor(target: str) -> bool:
    lower = target.strip().lower()
    return (
        not lower
        or lower.startswith("#")
        or lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
    )


def markdown_link_issues(repo_root: Path, paths: list[Path], *, current_wp_tokens: set[str] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    for source in paths:
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            if is_external_or_anchor(raw_target):
                continue
            if current_wp_tokens is not None:
                lowered_target = raw_target.lower()
                if not any(token in lowered_target for token in current_wp_tokens):
                    continue
            target = _strip_fragment_and_query(raw_target)
            if not target:
                continue
            resolved = (source.parent / target).resolve()
            try:
                resolved.relative_to(repo_root.resolve())
            except ValueError:
                issues.append(
                    Issue(
                        severity="warning",
                        code="external-local-link",
                        path=rel(source, repo_root),
                        message=f"link target leaves repository: {raw_target}",
                    )
                )
                continue
            if not resolved.exists():
                issues.append(
                    Issue(
                        severity="error",
                        code="broken-markdown-link",
                        path=rel(source, repo_root),
                        message=f"missing link target: {raw_target}",
                    )
                )
    return issues


def acceptance_index_paths(repo_root: Path, reviews: list[Path]) -> list[Path]:
    paths: list[Path] = []
    if not reviews or any("archive/wp-acceptance" not in path.as_posix() for path in reviews):
        paths.extend(
            [
                repo_root / REVIEW_DIR / "README.md",
                repo_root / REVIEW_DIR / "README.zh.md",
            ]
        )
    if any("archive/wp-acceptance" in path.as_posix() for path in reviews):
        paths.extend(
            [
                repo_root / REVIEW_DIR / "archive/wp-acceptance/README.md",
                repo_root / REVIEW_DIR / "archive/wp-acceptance/README.zh.md",
            ]
        )
    return paths


def downgrade_archived_link_issues(issues: list[Issue]) -> list[Issue]:
    return [
        Issue(
            severity="warning",
            code="archived-broken-markdown-link",
            path=issue.path,
            message=issue.message,
            owner=issue.owner,
        )
        if issue.severity == "error" and issue.code == "broken-markdown-link"
        else issue
        for issue in issues
    ]


def file_mentions_any(path: Path, needles: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return any(needle in text for needle in needles)


def canonical_task_doc_paths(audit: WpAudit, repo_root: Path) -> list[Path]:
    return sorted(
        repo_root / rel_path
        for rel_path in audit.task_docs
        if not rel_path.endswith(".zh.md")
    )


def canonical_acceptance_review_paths(audit: WpAudit, repo_root: Path) -> list[Path]:
    return sorted(
        repo_root / rel_path
        for rel_path in audit.acceptance_reviews
        if not rel_path.endswith(".zh.md")
    )


def read_task_status(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = STATUS_LINE_RE.match(raw_line)
        if match:
            return match.group(1).strip().replace("`", "")
    return None


def is_planned_stage(status_text: str | None) -> bool:
    return bool(status_text and re.search(r"\bplanned\b", status_text, re.IGNORECASE))


def build_required_zh_peer_status(repo_root: Path, paths: list[Path]) -> PeerStatus:
    required_total = 0
    required_present = 0
    missing_paths: list[str] = []
    for path in paths:
        if required_peer_kind(path) != "required":
            continue
        required_total += 1
        peer = zh_peer(path)
        if peer.exists():
            required_present += 1
        else:
            missing_paths.append(rel(peer, repo_root))
    return PeerStatus(
        required_total=required_total,
        required_present=required_present,
        required_missing=required_total - required_present,
        all_present=required_total == required_present,
        missing_paths=missing_paths,
    )


def build_readme_index_mentions(
    repo_root: Path,
    audit: WpAudit,
    folder: Path,
    canonical_review_paths: list[Path],
) -> list[MentionStatus]:
    mentions: list[MentionStatus] = []
    sim_readme_en = repo_root / SIM_ARCH_DIR / "README.md"
    sim_readme_zh = repo_root / SIM_ARCH_DIR / "README.zh.md"
    readme_needles = [folder.name, audit.wp]
    mentions.append(
        MentionStatus(
            path=rel(sim_readme_en, repo_root),
            applicable=True,
            mentioned=file_mentions_any(sim_readme_en, readme_needles),
            note=f"mentions {folder.name} or {audit.wp}",
        )
    )
    mentions.append(
        MentionStatus(
            path=rel(sim_readme_zh, repo_root),
            applicable=True,
            mentioned=file_mentions_any(sim_readme_zh, readme_needles),
            note=f"mentions {folder.name} or {audit.wp}",
        )
    )

    review_index_paths = acceptance_index_paths(repo_root, canonical_review_paths)
    if not canonical_review_paths:
        for path in review_index_paths:
            mentions.append(
                MentionStatus(
                    path=rel(path, repo_root),
                    applicable=False,
                    mentioned=False,
                    note="no acceptance review exists yet",
                )
            )
        return mentions

    review_names = [path.name for path in canonical_review_paths]
    for path in review_index_paths:
        if not path.exists():
            mentions.append(
                MentionStatus(
                    path=rel(path, repo_root),
                    applicable=True,
                    mentioned=False,
                    note="index file is missing",
                )
            )
            continue
        mentions.append(
            MentionStatus(
                path=rel(path, repo_root),
                applicable=True,
                mentioned=file_mentions_any(path, review_names),
                note=f"mentions {', '.join(review_names)}",
            )
        )
    return mentions


def build_closure_checklist(
    *,
    wp: str,
    planned_stage: bool,
    missing_acceptance_review_expected: bool,
    required_zh_peer_status: PeerStatus,
    readme_index_mentions: list[MentionStatus],
) -> list[str]:
    checklist = [
        "Generated summary is advisory only; canonical acceptance still belongs to the human-reviewed acceptance review.",
    ]
    if planned_stage and missing_acceptance_review_expected:
        checklist.append(f"Keep the acceptance review absent while {wp} remains in planned stage.")
    else:
        checklist.append("Do not treat the current summary as an acceptance decision.")

    if required_zh_peer_status.all_present:
        checklist.append("Required Chinese companions are present; re-run after any task-doc edit.")
    else:
        checklist.append(
            "Restore required Chinese companions before closure: "
            + ", ".join(required_zh_peer_status.missing_paths)
        )

    simulation_mentions = [
        item
        for item in readme_index_mentions
        if item.applicable and item.path.startswith("docs/task/simulation_architecture/")
    ]
    if any(not item.mentioned for item in simulation_mentions):
        checklist.append(
            "Sync simulation-architecture README mentions: "
            + ", ".join(item.path for item in simulation_mentions if not item.mentioned)
        )
    else:
        checklist.append("Simulation-architecture README mentions are present.")

    review_mentions = [item for item in readme_index_mentions if item.path.startswith("docs/task/review/")]
    if review_mentions and all(not item.applicable for item in review_mentions):
        checklist.append("Review README/index sync is deferred until an acceptance review exists.")
    elif any(item.applicable and not item.mentioned for item in review_mentions):
        checklist.append(
            "Sync review README/index mentions: "
            + ", ".join(item.path for item in review_mentions if item.applicable and not item.mentioned)
        )
    else:
        checklist.append("Review README/index mentions are present.")

    checklist.append("Never mark the WP accepted from generated output alone.")
    return checklist


def build_wp_closure_summary(repo_root: Path, audit: WpAudit) -> WpClosureSummary:
    repo_root = repo_root.resolve()
    if audit.folder is None:
        folder = repo_root / SIM_ARCH_DIR
    else:
        folder = repo_root / audit.folder
    canonical_task_docs = canonical_task_doc_paths(audit, repo_root)
    canonical_review_paths = canonical_acceptance_review_paths(audit, repo_root)
    all_canonical_paths = [*canonical_task_docs, *canonical_review_paths]
    primary_task_doc = canonical_task_docs[0] if canonical_task_docs else None
    task_status = read_task_status(primary_task_doc)
    planned_stage = is_planned_stage(task_status)
    required_zh_peer_status = build_required_zh_peer_status(repo_root, all_canonical_paths)
    readme_index_mentions = build_readme_index_mentions(repo_root, audit, folder, canonical_review_paths)
    acceptance_reviews_count = len(canonical_review_paths)
    missing_acceptance_review_expected = planned_stage and acceptance_reviews_count == 0
    checklist = build_closure_checklist(
        wp=audit.wp,
        planned_stage=planned_stage,
        missing_acceptance_review_expected=missing_acceptance_review_expected,
        required_zh_peer_status=required_zh_peer_status,
        readme_index_mentions=readme_index_mentions,
    )
    return WpClosureSummary(
        wp=audit.wp,
        wp_key=audit.wp_key,
        folder=audit.folder,
        primary_task_doc=rel(primary_task_doc, repo_root) if primary_task_doc else None,
        task_status=task_status,
        planned_stage=planned_stage,
        task_docs_count=len(audit.task_docs),
        canonical_task_docs_count=len(canonical_task_docs),
        acceptance_reviews_count=acceptance_reviews_count,
        missing_acceptance_review_expected=missing_acceptance_review_expected,
        required_zh_peer_status=required_zh_peer_status,
        readme_index_mentions=readme_index_mentions,
        checklist=checklist,
        authority_boundary="generated-summary-hint-only",
        canonical_authority="human-reviewed acceptance review",
    )


def audit_wp(repo_root: Path, wp_label: str) -> WpAudit:
    repo_root = repo_root.resolve()
    wp_key = normalize_wp_key(wp_label)
    wp = display_wp(wp_key)
    folders = discover_wp_folders(repo_root)
    folder = folders.get(wp_key)
    issues: list[Issue] = []

    if folder is None:
        issues.append(
            Issue(
                severity="error",
                code="missing-wp-folder",
                path=rel(repo_root / SIM_ARCH_DIR, repo_root),
                message=f"no task folder found for {wp}",
            )
        )
        return WpAudit(wp=wp, wp_key=wp_key, folder=None, task_docs=[], acceptance_reviews=[], issues=issues)

    task_docs = sorted(folder.glob("*.md"))
    canonical_task_docs = [path for path in task_docs if not path.name.endswith(".zh.md")]
    for path in canonical_task_docs:
        peer_kind = required_peer_kind(path)
        peer = zh_peer(path)
        if peer_kind == "required" and not peer.exists():
            issues.append(
                Issue(
                    severity="error",
                    code="missing-required-zh-peer",
                    path=rel(path, repo_root),
                    message=f"required Chinese companion is missing: {peer.name}",
                )
            )
        elif peer_kind == "optional" and not peer.exists():
            issues.append(
                Issue(
                    severity="warning",
                    code="missing-optional-zh-peer",
                    path=rel(path, repo_root),
                    message=f"optional Chinese companion is missing: {peer.name}",
                )
            )

    readme_en = repo_root / SIM_ARCH_DIR / "README.md"
    readme_zh = repo_root / SIM_ARCH_DIR / "README.zh.md"
    readme_needles = [folder.name, wp]
    if not file_mentions_any(readme_en, readme_needles):
        issues.append(
            Issue(
                severity="warning",
                code="simulation-readme-missing-wp",
                path=rel(readme_en, repo_root),
                message=f"simulation architecture README does not mention {wp} or {folder.name}",
            )
        )
    if not file_mentions_any(readme_zh, readme_needles):
        issues.append(
            Issue(
                severity="warning",
                code="simulation-readme-zh-missing-wp",
                path=rel(readme_zh, repo_root),
                message=f"Chinese simulation architecture README does not mention {wp} or {folder.name}",
            )
        )

    reviews = find_acceptance_reviews(repo_root, wp_key)
    canonical_reviews = [path for path in reviews if not path.name.endswith(".zh.md")]
    if not canonical_reviews:
        issues.append(
            Issue(
                severity="warning",
                code="missing-acceptance-review",
                path=rel(repo_root / REVIEW_DIR, repo_root),
                message=f"no acceptance review found for {wp}; leave this warning open until closure",
            )
        )
    for review in canonical_reviews:
        peer = zh_peer(review)
        if not peer.exists():
            issues.append(
                Issue(
                    severity="error",
                    code="missing-acceptance-zh-peer",
                    path=rel(review, repo_root),
                    message=f"required Chinese acceptance companion is missing: {peer.name}",
                )
            )

    if canonical_reviews:
        review_names = [review.name for review in canonical_reviews]
        for index in acceptance_index_paths(repo_root, reviews):
            if not index.exists():
                issues.append(
                    Issue(
                        severity="warning",
                        code="missing-review-index",
                        path=rel(index, repo_root),
                        message="review index file is missing",
                    )
                )
                continue
            if not file_mentions_any(index, review_names):
                issues.append(
                    Issue(
                        severity="warning",
                        code="review-index-missing-acceptance",
                        path=rel(index, repo_root),
                        message=f"review index does not mention {', '.join(review_names)}",
                    )
                )

    link_issues = markdown_link_issues(repo_root, sorted({p for p in [*task_docs, *reviews] if p.exists()}))
    if rel(folder, repo_root).startswith(f"{SIM_ARCH_DIR.as_posix()}/archive/"):
        link_issues = downgrade_archived_link_issues(link_issues)
    issues.extend(link_issues)
    index_link_tokens = {
        wp_key,
        wp.lower(),
        folder.name.lower(),
        *{review.name.lower() for review in reviews},
    }
    index_link_scope = [
        readme_en,
        readme_zh,
        *acceptance_index_paths(repo_root, reviews),
    ]
    issues.extend(
        markdown_link_issues(
            repo_root,
            sorted({p for p in index_link_scope if p.exists()}),
            current_wp_tokens=index_link_tokens,
        )
    )

    return WpAudit(
        wp=wp,
        wp_key=wp_key,
        folder=rel(folder, repo_root),
        task_docs=[rel(path, repo_root) for path in task_docs],
        acceptance_reviews=[rel(path, repo_root) for path in reviews],
        issues=issues,
    )


def severity_rank(severity: str) -> int:
    return {"error": 3, "warning": 2, "info": 1}.get(severity, 0)


def render_summary_report(summaries: list[WpClosureSummary]) -> str:
    lines: list[str] = []
    for summary in summaries:
        lines.append(f"## {summary.wp} Closure Summary")
        lines.append(f"folder: {summary.folder or '<missing>'}")
        lines.append(f"primary task doc: {summary.primary_task_doc or '<missing>'}")
        lines.append(f"task status: {summary.task_status or '<missing>'}")
        lines.append(
            "authority: "
            f"{summary.authority_boundary}; canonical acceptance remains the {summary.canonical_authority}."
        )
        lines.append(
            f"task docs: {summary.task_docs_count} total "
            f"(canonical: {summary.canonical_task_docs_count})"
        )
        lines.append(f"acceptance reviews (canonical): {summary.acceptance_reviews_count}")
        lines.append("planned stage: " + ("yes" if summary.planned_stage else "no"))
        lines.append(
            "missing acceptance review expected: "
            + ("yes (planned stage)" if summary.missing_acceptance_review_expected else "no")
        )
        peer = summary.required_zh_peer_status
        if peer.missing_paths:
            lines.append(
                f"required zh peers: {peer.required_present}/{peer.required_total} present; "
                f"missing: {', '.join(peer.missing_paths)}"
            )
        else:
            lines.append(f"required zh peers: {peer.required_present}/{peer.required_total} present")
        lines.append("README/index mentions:")
        for item in summary.readme_index_mentions:
            state = "mentioned" if item.mentioned else "not mentioned"
            if not item.applicable:
                state = "not applicable yet (no acceptance review)"
            lines.append(f"- {item.path}: {state}")
        lines.append("checklist:")
        for item in summary.checklist:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def print_text_report(audits: list[WpAudit]) -> None:
    for audit in audits:
        print(f"## {audit.wp} Closure Audit")
        print(f"folder: {audit.folder or '<missing>'}")
        print(f"task docs: {len(audit.task_docs)}")
        print(f"acceptance reviews: {len(audit.acceptance_reviews)}")
        if not audit.issues:
            print("issues: none")
            print()
            continue
        print("issues:")
        for issue in sorted(audit.issues, key=lambda item: (-severity_rank(item.severity), item.code, item.path)):
            print(f"- [{issue.severity}] {issue.code}: {issue.path} :: {issue.message}")
        print()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit WP task/review closure docs and emit a closure-subagent checklist.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--wp",
        action="append",
        help="Work package label to audit, e.g. WP9, wp9, WP7.5. Repeat to audit multiple WPs. Defaults to all discovered WP folders.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit a read-only generated closure summary instead of the issue-focused audit report.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when error-level issues are found.")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit non-zero when warning-level or worse issues are found.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.wp:
        wp_labels = args.wp
    else:
        wp_labels = sorted(discover_wp_folders(repo_root))

    audits = [audit_wp(repo_root, label) for label in wp_labels]
    if args.summary:
        summaries = [build_wp_closure_summary(repo_root, audit) for audit in audits]
        if args.json:
            print(json.dumps([asdict(summary) for summary in summaries], indent=2, ensure_ascii=False))
        else:
            print(render_summary_report(summaries), end="")
    else:
        if args.json:
            print(json.dumps([asdict(audit) for audit in audits], indent=2, ensure_ascii=False))
        else:
            print_text_report(audits)

    threshold = "warning" if args.fail_on_warning else "error"
    if args.strict or args.fail_on_warning:
        min_rank = severity_rank(threshold)
        if any(severity_rank(issue.severity) >= min_rank for audit in audits for issue in audit.issues):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
