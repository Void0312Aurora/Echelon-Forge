#!/usr/bin/env python3
"""Add the missing `Retention:` line to source-package manifests.

The raw-source rule requires every package under `raw/sources/<publisher>/<source_id>/`
to contain a manifest *and* a retention note
(`database/research/equipment/raw/README.md`). 43 of 193 packages carry no
`Retention:` line, all in the air domain.

The line is appended after the manifest's last metadata field, before any prose
section, using the dominant wording already in the tree.

Usage:
    python database/_work/backfill_manifest_retention.py --dry-run
    python database/_work/backfill_manifest_retention.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAW_SOURCES = Path(__file__).resolve().parents[1] / "research" / "equipment" / "raw" / "sources"

RETENTION_LINE = "Retention: manifest and extracted parameter notes only"
RETENTION_RE = re.compile(r"^Retention:", re.MULTILINE)
FIELD_RE = re.compile(r"^([A-Z][A-Za-z /]*?):", re.MULTILINE)


def targets() -> list[Path]:
    found = []
    for manifest in sorted(RAW_SOURCES.rglob("manifest.md")):
        text = manifest.read_text(encoding="utf-8")
        if not RETENTION_RE.search(text):
            found.append(manifest)
    return found


def insert_retention(text: str) -> str:
    """Append the retention line after the last metadata field."""
    fields = list(FIELD_RE.finditer(text))
    if not fields:
        # Nothing to anchor on: put it before the first section heading.
        heading = re.search(r"^## ", text, re.MULTILINE)
        anchor = heading.start() if heading else len(text)
        return text[:anchor] + RETENTION_LINE + "\n\n" + text[anchor:]
    last = fields[-1]
    line_end = text.find("\n", last.end())
    if line_end == -1:
        return text.rstrip("\n") + "\n" + RETENTION_LINE + "\n"
    return text[:line_end] + "\n" + RETENTION_LINE + text[line_end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    found = targets()
    if not found:
        print("nothing to backfill")
        return 0

    for manifest in found:
        text = manifest.read_text(encoding="utf-8")
        updated = insert_retention(text)
        if updated == text:
            print(f"SKIP (no anchor) {manifest.parent.name}")
            continue
        action = "would add" if args.dry_run else "added"
        print(f"{action} {manifest.parent.name}")
        if args.apply:
            manifest.write_text(updated, encoding="utf-8", newline="\n")

    print()
    print(f"{len(found)} manifest(s) {'reported' if args.dry_run else 'updated'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
