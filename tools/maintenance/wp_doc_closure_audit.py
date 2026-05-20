#!/usr/bin/env python3
"""Audit simulation-architecture WP closure docs without rewriting them.

The tool is intentionally read-only. It produces a handoff checklist for a
documentation closure worker instead of making the main implementation path
manually synchronize README, review, archive, and bilingual links.
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
    for path in sorted(sim_dir.iterdir()):
        if not path.is_dir() or not path.name.startswith("wp"):
            continue
        try:
            out[normalize_wp_key(path.name)] = path
        except ValueError:
            continue
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
    paths = [
        repo_root / REVIEW_DIR / "README.md",
        repo_root / REVIEW_DIR / "README.zh.md",
    ]
    if any("archive/wp-acceptance" in path.as_posix() for path in reviews):
        paths.extend(
            [
                repo_root / REVIEW_DIR / "archive/wp-acceptance/README.md",
                repo_root / REVIEW_DIR / "archive/wp-acceptance/README.zh.md",
            ]
        )
    return paths


def file_mentions_any(path: Path, needles: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return any(needle in text for needle in needles)


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

    issues.extend(markdown_link_issues(repo_root, sorted({p for p in [*task_docs, *reviews] if p.exists()})))
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
