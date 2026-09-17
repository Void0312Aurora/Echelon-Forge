#!/usr/bin/env python3
"""Backfill `Equipment ID` metadata into catalog leaves that lack it.

Scope: leaves that already carry a parameter table but no identity line. Stub
leaves (no parameter table) are out of scope, because a leaf with nothing
extracted has nothing to bind to a queue row yet.

The inserted line is an additive metadata row, not a new section. That keeps the
change independent of the parameter-table shape question: this script does not
touch a table header, a column, or a value.

Usage:
    python database/_work/backfill_equipment_id.py --dry-run
    python database/_work/backfill_equipment_id.py --apply
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

EQUIPMENT = Path(__file__).resolve().parents[1] / "research" / "equipment"
CATALOG = EQUIPMENT / "catalog"
BACKLOG = EQUIPMENT / "backlog"

EQUIPMENT_ID_LINE = re.compile(
    r"Equipment ID\s*[:|]\s*`?([^`|\n]+?)`?\s*\|?\s*$",
    re.MULTILINE,
)
LAST_VERIFIED_LINE = re.compile(r"^Last verified:.*$", re.MULTILINE)


def backfill_targets() -> list[tuple[str, str, Path]]:
    """Return (equipment_id, queue_name, leaf_path) for every leaf to backfill."""
    targets: list[tuple[str, str, Path]] = []
    for queue in sorted(BACKLOG.glob("*.csv")):
        with queue.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") == "held":
                    continue
                rel = row["catalog_path"].removeprefix("catalog/").strip("/")
                if not rel:
                    continue
                leaf = CATALOG / rel / "README.md"
                if not leaf.exists():
                    continue
                text = leaf.read_text(encoding="utf-8")
                if "## Parameters" not in text:
                    continue
                if EQUIPMENT_ID_LINE.search(text):
                    continue
                targets.append((row["equipment_id"], queue.name, leaf))
    return targets


def insert_line(text: str, equipment_id: str) -> str:
    """Insert the identity row immediately after the Last verified metadata line."""
    line = f"Equipment ID: `{equipment_id}`"
    match = LAST_VERIFIED_LINE.search(text)
    if match:
        end = match.end()
        return text[:end] + "\n" + line + text[end:]
    # No metadata block to anchor on: place it before the first section heading.
    heading = re.search(r"^## ", text, re.MULTILINE)
    if heading:
        return text[: heading.start()] + line + "\n\n" + text[heading.start() :]
    return text.rstrip("\n") + "\n\n" + line + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    targets = backfill_targets()
    if not targets:
        print("nothing to backfill")
        return 0

    for equipment_id, queue_name, leaf in targets:
        text = leaf.read_text(encoding="utf-8")
        updated = insert_line(text, equipment_id)
        if updated == text:
            print(f"SKIP (no anchor) {equipment_id} {leaf}")
            continue
        action = "would insert" if args.dry_run else "inserted"
        print(f"{action} {equipment_id} -> {leaf.parent.relative_to(CATALOG).as_posix()}")
        if args.apply:
            leaf.write_text(updated, encoding="utf-8", newline="\n")

    print()
    print(f"{len(targets)} leaf/leaves {'reported' if args.dry_run else 'updated'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
