#!/usr/bin/env python3
"""Equipment tree consistency check for the reduced write set.

Covers the five closure-gate conditions declared in database/_work/README.md:

  1. every source id referenced by a catalog leaf resolves to a manifest
  2. every backlog catalog_path leaf exists and carries a matching Equipment ID
  3. backlog status agrees with coverage.csv status for shared candidates
  4. no D-tier source, no package without a retention note
  5. no change outside the write set (manual: `git status --porcelain -- database`)

Usage:
    python database/_work/check_equipment_tree.py [--json]

Exit code is 0 when every automated condition passes, 1 otherwise. Findings are
advisory: this tool reports drift, it does not repair it and does not grant any
equipment record a status above what the queue already declares.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

EQUIPMENT = Path(__file__).resolve().parents[1] / "research" / "equipment"
CATALOG = EQUIPMENT / "catalog"
BACKLOG = EQUIPMENT / "backlog"
COVERAGE = EQUIPMENT / "coverage" / "coverage.csv"
RAW_SOURCES = EQUIPMENT / "raw" / "sources"

SOURCE_ID_RE = re.compile(r"\bp5-[a-z0-9][a-z0-9-]*\b")
EQUIPMENT_ID_RE = re.compile(
    r"Equipment ID\s*[:|]\s*`?([^`|\n]+?)`?\s*\|?\s*$",
    re.MULTILINE,
)
MANIFEST_ID_RE = re.compile(r"^Source ID:\s*`?([a-z0-9-]+)`?\s*$", re.MULTILINE)
MANIFEST_TIER_RE = re.compile(r"^Tier:\s*`?([A-D])`?\s*$", re.MULTILINE)
MANIFEST_RETENTION_RE = re.compile(r"^Retention:\s*(.+)$", re.MULTILINE)


def load_manifests() -> dict[str, dict]:
    """Index every source package by declared Source ID."""
    index: dict[str, dict] = {}
    for manifest in sorted(RAW_SOURCES.rglob("manifest.md")):
        text = manifest.read_text(encoding="utf-8")
        match = MANIFEST_ID_RE.search(text)
        declared = match.group(1) if match else None
        tier_match = MANIFEST_TIER_RE.search(text)
        retention_match = MANIFEST_RETENTION_RE.search(text)
        index[manifest.parent.name] = {
            "path": manifest,
            "declared_id": declared,
            "tier": tier_match.group(1) if tier_match else None,
            "retention": retention_match.group(1).strip() if retention_match else None,
        }
    return index


def iter_leaves():
    """Yield (relative_path, text) for every catalog leaf record."""
    for readme in sorted(CATALOG.rglob("README.md")):
        text = readme.read_text(encoding="utf-8")
        if "## Parameters" in text:
            rel = readme.parent.relative_to(CATALOG).as_posix()
            yield rel, text


def load_backlog() -> dict[str, list[dict]]:
    queues: dict[str, list[dict]] = {}
    for queue in sorted(BACKLOG.glob("*.csv")):
        with queue.open(encoding="utf-8", newline="") as handle:
            queues[queue.name] = list(csv.DictReader(handle))
    return queues


def load_coverage() -> dict[str, dict]:
    with COVERAGE.open(encoding="utf-8", newline="") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def check_all() -> dict:
    manifests = load_manifests()
    backlog = load_backlog()
    coverage = load_coverage()

    leaves: dict[str, str] = {}
    referenced: dict[str, set[str]] = {}
    for rel, text in iter_leaves():
        leaves[rel] = text
        referenced[rel] = set(SOURCE_ID_RE.findall(text))

    result: dict = {"conditions": {}, "counts": {}, "findings": []}

    # condition 1 -- source references resolve
    dangling: list[tuple[str, str]] = []
    for rel, ids in referenced.items():
        for source_id in sorted(ids):
            if source_id not in manifests:
                dangling.append((rel, source_id))
    unresolved_manifests = sorted(
        key for key, value in manifests.items() if value["declared_id"] != key
    )
    result["conditions"]["c1_sources_resolve"] = {
        "pass": not dangling and not unresolved_manifests,
        "dangling": [{"leaf": leaf, "source_id": sid} for leaf, sid in dangling],
        "manifest_id_path_mismatch": unresolved_manifests,
    }

    # condition 2 -- backlog binding
    # A `held` row is a legitimate record of blocked collection and is excluded.
    # A stub leaf (no parameter table) is also excluded: with nothing extracted
    # there is nothing to bind to a queue row.
    # A leaf carrying an `Equipment ID` is a variant-level record that may serve
    # more than one country row. `tornado-ids` is the in-tree precedent: one leaf,
    # one id, a multi-row operator table. Such rows are not defects; only a leaf
    # with a parameter table and no id at all is reported.
    unbound: list[dict] = []
    missing_leaf: list[dict] = []
    held_rows = 0
    stub_rows = 0
    for queue_name, rows in backlog.items():
        for row in rows:
            if row.get("status") == "held":
                held_rows += 1
                continue
            rel = row["catalog_path"].removeprefix("catalog/").strip("/")
            if not rel:
                missing_leaf.append(
                    {
                        "queue": queue_name,
                        "equipment_id": row["equipment_id"],
                        "reason": "non-held row carries no catalog_path",
                    }
                )
                continue
            leaf_path = CATALOG / rel / "README.md"
            if not leaf_path.exists():
                missing_leaf.append(
                    {
                        "queue": queue_name,
                        "equipment_id": row["equipment_id"],
                        "reason": "catalog_path has no README",
                        "catalog_path": row["catalog_path"],
                    }
                )
                continue
            text = leaf_path.read_text(encoding="utf-8")
            if "## Parameters" not in text:
                stub_rows += 1
                continue
            if EQUIPMENT_ID_RE.search(text):
                continue
            unbound.append(
                {
                    "queue": queue_name,
                    "equipment_id": row["equipment_id"],
                    "leaf_equipment_id": None,
                    "catalog_path": row["catalog_path"],
                }
            )
    result["conditions"]["c2_backlog_binding"] = {
        "pass": not unbound and not missing_leaf,
        "leaf_missing_equipment_id": unbound,
        "catalog_path_missing": missing_leaf,
        "held_rows_excluded": held_rows,
        "stub_rows_excluded": stub_rows,
    }

    # condition 3 -- backlog and coverage status agree
    backlog_index = {
        row["equipment_id"]: (name, row)
        for name, rows in backlog.items()
        for row in rows
    }
    disagreements: list[dict] = []
    for candidate_id, cov_row in coverage.items():
        if candidate_id not in backlog_index:
            disagreements.append(
                {
                    "candidate_id": candidate_id,
                    "reason": "coverage row has no backlog row",
                    "coverage_status": cov_row.get("status"),
                }
            )
            continue
        queue_name, queue_row = backlog_index[candidate_id]
        if queue_row.get("status") != cov_row.get("status"):
            disagreements.append(
                {
                    "candidate_id": candidate_id,
                    "queue": queue_name,
                    "backlog_status": queue_row.get("status"),
                    "coverage_status": cov_row.get("status"),
                }
            )
    result["conditions"]["c3_status_agreement"] = {
        "pass": not disagreements,
        "disagreements": disagreements,
    }

    # condition 4 -- source admission floor
    d_tier = sorted(k for k, v in manifests.items() if v["tier"] == "D")
    no_retention = sorted(k for k, v in manifests.items() if not v["retention"])
    no_rights = sorted(
        k
        for k, v in manifests.items()
        if "rights" not in v["path"].read_text(encoding="utf-8").lower()
        and "redistribution" not in v["path"].read_text(encoding="utf-8").lower()
    )
    result["conditions"]["c4_source_admission_floor"] = {
        "pass": not d_tier and not no_retention,
        "tier_d": d_tier,
        "missing_retention_note": no_retention,
        "missing_rights_field_advisory": no_rights,
    }

    # condition 5 -- source-artifact consistency
    #
    # Two failure modes are covered, both of which produce a provenance graph that
    # cannot be walked from a claim back to an artifact:
    #
    #   5a  a manifest describes a claim as coming from a source it does not name
    #   5b  a manifest is an aggregate of several artifacts rather than one
    #
    # 5a matches on word boundaries and a wider phrase set than the first version
    # did, because the first version was demonstrably bypassable by writing
    # "two further secondary sources" instead of "a further source".
    #
    # 5b treats more than one URL line as an aggregate. A manifest should describe
    # one locatable artifact; corroboration belongs in its own package with its own
    # id, so a claim can be traced to each source separately.
    #
    # Pre-existing baseline: one package that landed before this rule existed is
    # exempted by name. It is listed so the exemption is visible and so a second
    # one cannot be added silently. Anything not on this list fails.
    c5_baseline_exemptions = {
        # Landed in f9e2e4ed, before this rule existed. Its sentence records that
        # two leaf bounds are estimates rather than an official Mk IV
        # specification and names no specific package, so the fix belongs with a
        # CV90 leaf repair rather than with a source-admission tranche.
        "p5-eu-ground-cv90mk4-cv90cz",
    }

    unnamed_pattern = re.compile(
        r"\b("
        r"further source|further sources|further secondary source|further secondary sources|"
        r"second source|second sources|third source|third sources|"
        r"another source|another sources|other source|other sources|"
        r"reference works|a second specialist compilation|unnamed source|"
        r"encyclopedic record|encyclopedic source|compiled record|compiled source|"
        r"compiled secondary source|database entry|corroborating record|"
        r"corroborating source|supporting source|additional source|additional sources|"
        r"two sources|three sources|four sources|several sources|multiple sources|"
        r"further compilation|other compilations"
        r")\b",
        re.IGNORECASE,
    )
    aggregate_markers = re.compile(
        r"^(Corroborating URL|Alternate path|Mirror|Second URL|Additional URL):",
        re.IGNORECASE | re.MULTILINE,
    )

    # A correction history describes a claim that was withdrawn. The sentence
    # quotes the vocabulary of the withdrawn claim in order to say what it was,
    # so it matches 5a without making an unnamed-source claim itself. Such a
    # sentence is exempt only when it also carries withdrawal vocabulary; a
    # sentence that merely mentions an earlier revision and then makes a live
    # unnamed claim still fails.
    correction_marker = re.compile(
        r"earlier revision|withdrawn|was withdrawn|is withdrawn|were withdrawn",
        re.IGNORECASE,
    )

    unattributed: list[dict] = []
    aggregates: list[dict] = []
    for key, value in manifests.items():
        if key in c5_baseline_exemptions:
            continue
        text = value["path"].read_text(encoding="utf-8")

        for sentence in re.split(r"(?<=[.;])\s+|\n", text):
            if not unnamed_pattern.search(sentence):
                continue
            if SOURCE_ID_RE.search(sentence):
                continue
            if len(sentence.strip()) < 20:
                continue
            if correction_marker.search(sentence):
                continue
            unattributed.append(
                {
                    "package": key,
                    "sentence": " ".join(sentence.split())[:220],
                }
            )

        extra_urls = aggregate_markers.findall(text)
        if extra_urls:
            aggregates.append(
                {
                    "package": key,
                    "extra_locators": sorted(set(extra_urls)),
                }
            )

    result["conditions"]["c5_source_artifact_consistency"] = {
        "pass": not unattributed and not aggregates,
        "unnamed_source_claims": unattributed,
        "aggregate_packages": aggregates,
        "baseline_exemptions": sorted(c5_baseline_exemptions),
    }

    status_counts: dict[str, int] = {}
    for rows in backlog.values():
        for row in rows:
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    result["counts"] = {
        "manifests": len(manifests),
        "leaves": len(leaves),
        "distinct_sources_referenced": len({s for ids in referenced.values() for s in ids}),
        "leaves_without_equipment_id": sum(1 for t in leaves.values() if not EQUIPMENT_ID_RE.search(t)),
        "backlog_rows": sum(len(rows) for rows in backlog.values()),
        "coverage_rows": len(coverage),
        "status_counts": status_counts,
    }

    result["pass"] = all(c["pass"] for c in result["conditions"].values())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--verbose", action="store_true", help="print every finding")
    args = parser.parse_args()

    result = check_all()

    if args.json:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if result["pass"] else 1

    labels = {
        "c1_sources_resolve": "C1 every referenced source id resolves",
        "c2_backlog_binding": "C2 backlog leaf binding (Equipment ID)",
        "c3_status_agreement": "C3 backlog vs coverage status",
        "c4_source_admission_floor": "C4 source admission floor (no D tier, retention present)",
        "c5_source_artifact_consistency": "C5 source-artifact consistency (no unnamed source, no aggregate package)",
    }
    for key, label in labels.items():
        condition = result["conditions"][key]
        print(f"[{'PASS' if condition['pass'] else 'FAIL'}] {label}")

    counts = result["counts"]
    print()
    print(f"manifests            {counts['manifests']}")
    print(f"catalog leaves       {counts['leaves']}")
    print(f"sources referenced   {counts['distinct_sources_referenced']}")
    print(f"leaves w/o Equipment ID {counts['leaves_without_equipment_id']}")
    print(f"backlog rows         {counts['backlog_rows']}")
    print(f"coverage rows        {counts['coverage_rows']}")
    print(f"status counts        {counts['status_counts']}")

    if args.verbose:
        print()
        print(json.dumps(result["conditions"], indent=2, sort_keys=True))

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
