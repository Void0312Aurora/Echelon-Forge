from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]

APPROVED_DIAGNOSTICS_TOP_LEVEL = {
  "__init__.py",
  "ablate_visual_training_effect.py",
  "air_combat_weapon_employment_process_probe.py",
  "arma_proxy_backend_stub.py",
  "benchmark.py",
  "benchmark_registry.py",
  "common.py",
  "cooperative_trajectory_base.py",
  "diagnose_cooperative_trajectory.py",
  "event_credit_head_probe.py",
  "fire_timing_fault_localization_probe.py",
  "flight_trajectory_diagnostics.py",
  "leader_perf_probe.py",
  "run_benchmark_suite.py",
  "trace_training_nonfinite_source.py",
}

FORBIDDEN_NAME_EXCEPTIONS = {
  "benchmark_registry.py",
  "run_benchmark_suite.py",
}

RETIRED_TOOL_ENTRYPOINTS = {
  "/".join(parts)
  for parts in (
    ("tools", "diagnostics", "air_combat_fire_timing_learnability_audit.py"),
    ("tools", "diagnostics", "air_combat_post_launch_assessment_benchmark.py"),
    ("tools", "diagnostics", "arma_proxy_backend_echelon_env.py"),
    ("tools", "diagnostics", "diagnose_runway_drift_sweep.py"),
    ("tools", "diagnostics", "diagnose_takeoff_to_landing_trajectory.py"),
    ("tools", "eval", "eval_naval_n4_baseline.py"),
    ("tools", "eval", "eval_sb3.py"),
  )
}

TEXT_SUFFIXES = {
  ".cfg",
  ".json",
  ".md",
  ".ps1",
  ".py",
  ".sh",
  ".toml",
  ".txt",
  ".yaml",
  ".yml",
}


def _repo_relative(path: Path) -> str:
  return path.relative_to(REPO_ROOT).as_posix()


def _iter_text_files() -> list[Path]:
  this_file = Path(__file__).resolve()
  roots = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "README.zh.md",
    REPO_ROOT / "docs",
    REPO_ROOT / "examples",
    REPO_ROOT / "scripts",
    REPO_ROOT / "tests",
    REPO_ROOT / "tools",
  ]
  files: list[Path] = []
  for root in roots:
    if root.is_file():
      if root.resolve() != this_file:
        files.append(root)
      continue
    if not root.exists():
      continue
    for path in root.rglob("*"):
      if path.is_file() and path.resolve() != this_file and path.suffix in TEXT_SUFFIXES:
        files.append(path)
  return files


@pytest.mark.xfail(
  strict=True,
  reason=(
    "lineage gap (governed at I57): the tools/diagnostics/ top-level "
    "'governed by function' consolidation to the APPROVED_DIAGNOSTICS_TOP_LEVEL "
    "15-entry set never landed on this lineage. Eleven ad-hoc top-level "
    "diagnostics scripts (kill_chain_*, mlf9_statistical_trends, "
    "lethality_chain_contract, structural_breakup_export, "
    "calibration_admission_audit) remain uncollapsed. The allowlist cannot be "
    "widened to include them without blessing the exact top-level sprawl this "
    "guard exists to forbid, so the guard intent is genuinely unmet here rather "
    "than merely relocated. See "
    "docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md section 5/8."
  ),
)
def test_diagnostics_top_level_entrypoints_are_governed_by_function() -> None:
  diagnostics_dir = REPO_ROOT / "tools" / "diagnostics"
  actual = {path.name for path in diagnostics_dir.glob("*.py")}

  assert actual == APPROVED_DIAGNOSTICS_TOP_LEVEL

  forbidden_name_parts = (
    "benchmark_",
    "m3s",
    "n4",
    "phase",
    "post_launch_assessment_benchmark",
    "runway_drift",
    "stage",
    "takeoff_to_landing",
  )
  unexpected = [
    name
    for name in sorted(actual)
    if any(part in name.lower() for part in forbidden_name_parts)
    and name not in FORBIDDEN_NAME_EXCEPTIONS
  ]

  assert unexpected == []


def test_benchmark_families_are_registered_modules() -> None:
  from tools.diagnostics.benchmark_registry import BENCHMARK_FAMILIES

  benchmarks_dir = REPO_ROOT / "tools" / "diagnostics" / "benchmarks"
  benchmark_modules = {
    path.stem
    for path in benchmarks_dir.glob("*.py")
    if path.name != "__init__.py"
  }

  assert set(BENCHMARK_FAMILIES) == benchmark_modules

  for name, family in BENCHMARK_FAMILIES.items():
    assert family.name == name
    assert family.module_path == f"tools.diagnostics.benchmarks.{name}"
    assert (benchmarks_dir / f"{name}.py").is_file()


def test_retired_wrapper_entrypoints_do_not_reappear_or_remain_referenced() -> None:
  for entrypoint in RETIRED_TOOL_ENTRYPOINTS:
    assert not REPO_ROOT.joinpath(entrypoint).exists(), entrypoint

  offenders: dict[str, list[str]] = {}
  for path in _iter_text_files():
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits = [entrypoint for entrypoint in RETIRED_TOOL_ENTRYPOINTS if entrypoint in text]
    if hits:
      offenders[_repo_relative(path)] = hits

  assert offenders == {}


def test_tools_governance_docs_record_extension_points() -> None:
  tools_readme = (REPO_ROOT / "tools" / "README.md").read_text(encoding="utf-8")
  diagnostics_readme = (REPO_ROOT / "tools" / "diagnostics" / "README.md").read_text(encoding="utf-8")
  governance_matrix = (
    REPO_ROOT / "docs" / "engineering" / "automation" / "reviews" / "tools_script_governance_matrix_20260611.zh.md"
  ).read_text(encoding="utf-8")

  for text in (tools_readme, diagnostics_readme, governance_matrix):
    assert "tools/diagnostics/benchmark.py" in text
    assert "tools/diagnostics/fire_timing_fault_localization_probe.py --mode" in text
    assert "tools/diagnostics/flight_trajectory_diagnostics.py --mode" in text

  assert "新增 benchmark 进 `benchmarks/` 和 registry" in governance_matrix
