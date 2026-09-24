#!/usr/bin/env python3
"""Materialize the equipment source index from source manifests.

The output is deliberately a small audit index. It does not copy source
payloads and it does not infer missing rights, scope, or retrieval evidence.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "research" / "equipment"
SOURCE_ROOT = ROOT / "raw" / "sources"
OUTPUT = ROOT / "sources" / "ledger" / "ledger.csv"

FIELDS = [
    "source_id",
    "tier",
    "publisher",
    "author_or_maintainer",
    "title",
    "url",
    "domain",
    "equipment",
    "configuration",
    "provenance_status",
    "rights_status",
    "retrieval_status",
    "authority_status",
    "scope_status",
    "residual_status",
    "manifest_path",
]


def value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip().strip("`") if match else ""


def retrieval_status(text: str) -> str:
    block = re.search(r"^Retrieval:\s*\n((?:^[ \t]+\S.*\n?)+)", text, re.MULTILINE)
    if not block:
        return "not_recorded"
    match = re.search(r"^\s+status:\s*(\S+)\s*$", block.group(1), re.MULTILINE)
    return match.group(1) if match else "malformed"


def build_row(manifest: Path) -> dict[str, str]:
    text = manifest.read_text(encoding="utf-8")
    source_id = value(text, "Source ID") or manifest.parent.name
    configuration = value(text, "Configuration") or value(text, "Configuration boundary")
    rights_status = value(text, "Rights status") or "not_recorded"
    scope_status = value(text, "Scope status") or (
        "complete" if value(text, "Domain") and value(text, "Equipment") and configuration else "partial"
    )
    retrieval = retrieval_status(text)
    provenance_status = value(text, "Provenance status") or (
        "manifest+retrieval+retention"
        if retrieval not in {"not_recorded", "malformed"} and value(text, "Retention")
        else "manifest+retention"
        if value(text, "Retention")
        else "manifest_locator_only"
    )
    residual_status = value(text, "Residual status") or ("open" if (
        rights_status == "not_recorded"
        or retrieval in {"not_recorded", "malformed", "failed", "not_attempted", "no_record"}
        or re.search(r"did_not_return|unresolved|unknown|open gap|remaining uncertainty", text, re.IGNORECASE)
    ) else "review")
    relative = manifest.relative_to(ROOT).as_posix()
    return {
        "source_id": source_id,
        "tier": value(text, "Tier"),
        "publisher": value(text, "Publisher"),
        "author_or_maintainer": value(text, "Author / maintainer"),
        "title": value(text, "Title"),
        "url": value(text, "URL"),
        "domain": value(text, "Domain"),
        "equipment": value(text, "Equipment"),
        "configuration": configuration,
        "provenance_status": provenance_status,
        "rights_status": rights_status,
        "retrieval_status": retrieval,
        "authority_status": "non-authoritative",
        "scope_status": scope_status,
        "residual_status": residual_status,
        "manifest_path": relative,
    }


def main() -> None:
    rows = [build_row(path) for path in sorted(SOURCE_ROOT.rglob("manifest.md"))]
    rows.sort(key=lambda row: row["source_id"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} source rows to {OUTPUT}")


if __name__ == "__main__":
    main()
