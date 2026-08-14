from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]

# These checks used to read the WP2.5/WP6/WP7 packages under
# docs/task/simulation_architecture/archive/, through a fallback that rewrote a
# live path into its archived twin. That tree was retired on 2026-08-13 (see
# docs/archive_ledger.md), and the fallback went with it. Each rule below is
# now asserted where it is still enforceable: the maintained architecture
# standard that inherited the decision.


def _text(*parts: str) -> str:
  path = REPO_ROOT.joinpath(*parts)
  assert path.is_file(), f"missing documentation path: {path.relative_to(REPO_ROOT)}"
  return path.read_text(encoding="utf-8")


def test_clock_merge_policy_name_is_distinct_from_cross_layer_merge_policy() -> None:
  architecture = _text(
    "docs",
    "architecture",
    "standards",
    "simulation_system_architecture_design.md",
  )

  assert "clock_merge_policy" in architecture
  assert "Reserve `merge_policy` for cross-layer request contracts" in architecture


def test_runtime_capabilities_trigger_stays_dormant_without_maintained_non_reference_profile() -> None:
  architecture = _text(
    "docs",
    "architecture",
    "standards",
    "simulation_system_architecture_design.md",
  )
  architecture_zh = _text(
    "docs",
    "architecture",
    "standards",
    "simulation_system_architecture_design.zh.md",
  )

  assert "Richer projection must not start until at least one non-reference" in architecture
  assert "更丰富的 projection 只有在至少一个" in architecture_zh


def test_runtime_facade_docs_record_diagnostics_surface_and_split_threshold() -> None:
  readme = _text("src", "runtime", "facade", "README.md")
  readme_zh = _text("src", "runtime", "facade", "README.zh.md")

  for text in (readme, readme_zh):
    assert "DiagnosticsTrace" in text
    assert "export_engagement_event_packet()" in text
    assert "roughly 40 methods" in text or "约 40 个" in text
    for group in (
      "Session",
      "Setup",
      "Execution",
      "Observation",
      "Diagnostics",
      "Engagement",
      "Capability",
    ):
      assert group in text
