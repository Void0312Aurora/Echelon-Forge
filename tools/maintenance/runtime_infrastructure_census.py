"""Reproducible physical LOC census and source target graph for issue #126.

Only tracked source is counted. Blank/comment lines are included. This is a
maintenance-cost inventory, not runtime profiling or proof of dead code.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import subprocess

from tools.architecture.cmake_target_graph import build_edges

ROOT = Path(__file__).resolve().parents[2]
EXTENSIONS = {".h", ".hpp", ".cpp", ".cc", ".cxx"}
GROUPS = (
    "src/runtime/host", "src/runtime/contracts", "src/runtime/facade", "src/runtime/composition",
    "src/systems/physics", "src/systems/domains/air", "src/systems/domains/naval", "src/systems/domains/ground",
    "src/models/domains/air", "src/models/domains/naval", "src/models/domains/ground",
    "src/components/domains/air", "src/components/domains/naval", "src/components/domains/ground",
    "src/core", "src/content", "src/interfaces", "src/tools", "src/models", "src/components", "src/systems",
)


def _group(path: str) -> str:
    return next((group for group in GROUPS if path.startswith(group + "/")), "src/other")


def _exclusion(path: str) -> str | None:
    parts = Path(path).parts
    if "tests" in parts or "test" in parts:
        return "tests"
    if any(part.lower() in {"vendor", "third_party", "third-party", "external"} for part in parts):
        return "vendor"
    if any(part in {"generated", "_generated"} for part in parts) or Path(path).name.endswith((".generated.h", ".gen.h")):
        return "generated"
    return None


def census() -> dict:
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", "src"], cwd=ROOT).decode("utf-8").split("\0")
    rows = []
    groups: dict[str, Counter] = {}
    exclusions = Counter()
    for relative in sorted(path for path in tracked if path and Path(path).suffix in EXTENSIONS):
        path = ROOT / relative
        lines = len(path.read_text(encoding="utf-8").splitlines())
        excluded = _exclusion(relative)
        rows.append({"path": relative, "physical_loc": lines, "exclusion": excluded})
        exclusions[excluded or "included"] += lines
        if excluded is None:
            groups.setdefault(_group(relative), Counter()).update(files=1, physical_loc=lines)
    inclusive = {}
    for group in GROUPS[:6]:
        matching = [row for row in rows if row["path"].startswith(group + "/")]
        inclusive[group] = {"files": len(matching), "physical_loc": sum(row["physical_loc"] for row in matching)}
    edges = [{**asdict(edge), "path": "CMakeLists.txt"} for edge in build_edges(ROOT / "CMakeLists.txt")]
    graph: dict[str, set[str]] = {}
    for edge in edges:
        graph.setdefault(edge["source"], set()).add(edge["target"])
    reachable = {}
    for entry in ("ef_py", "ef_facade", "ef_runtime_kernel_candidate"):
        pending, seen = [entry], set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(graph.get(current, ()))
        reachable[entry] = sorted(seen)
    return {
        "schema_version": "echelon_forge.runtime_infrastructure_census.v1",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": {"root": "tracked src/", "extensions": sorted(EXTENSIONS),
                  "loc": "physical splitlines, including blanks/comments; no logical LOC claim",
                  "excluded": "tests/test directory, vendor/third_party/third-party/external directory, generated/_generated directory, *.generated.h/*.gen.h",
                  "target_graph": "existing source CMake scanner; syntactic union of branches, excludes variable/generator-expression resolution",
                  "domain_comparison": "folder ownership only; shared physics/core/models are not assigned to a complete domain capability"},
        "totals": {"tracked_files": len(rows), "inclusive_physical_loc": sum(row["physical_loc"] for row in rows),
                   "maintained_files": sum(row["exclusion"] is None for row in rows),
                   "maintained_physical_loc": exclusions["included"], "excluded_loc": dict(sorted(exclusions.items()))},
        "inclusive_issue_snapshot_folders": inclusive,
        "maintained_groups": dict(sorted(groups.items())),
        "target_edges": edges, "source_target_reachability": reachable,
        "files": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true", help="Omit individual file rows for the committed summary")
    args = parser.parse_args()
    report = census()
    if args.compact:
        report.pop("files")
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"totals": report["totals"], "groups": report["inclusive_issue_snapshot_folders"]}))


if __name__ == "__main__":
    main()
