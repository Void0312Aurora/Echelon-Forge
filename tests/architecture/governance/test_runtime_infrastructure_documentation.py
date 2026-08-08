from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _text(*parts: str) -> str:
  path = REPO_ROOT.joinpath(*parts)
  if path.is_file():
    return path.read_text(encoding="utf-8")

  if len(parts) > 3 and parts[:3] == (
    "docs",
    "task",
    "simulation_architecture",
  ):
    archived = REPO_ROOT.joinpath(
      "docs",
      "task",
      "simulation_architecture",
      "archive",
      *parts[3:],
    )
    if archived.is_file():
      return archived.read_text(encoding="utf-8")

  raise AssertionError(f"missing documentation path: {path.relative_to(REPO_ROOT)}")


def test_wp25_clock_merge_policy_name_is_distinct_from_cross_layer_merge_policy() -> None:
  scheduler = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp25_scheduler_semantics",
    "scheduler_semantics_wp25_20260519.md",
  )
  architecture = _text(
    "docs",
    "architecture",
    "standards",
    "simulation_system_architecture_design.md",
  )

  assert "clock_merge_policy" in scheduler
  assert "clock_merge_policy" in architecture
  assert "request field `merge_policy`" in scheduler
  assert "Reserve `merge_policy` for cross-layer request contracts" in architecture


def test_wp25_manifest_registry_examples_cover_all_p0_to_p10_stages() -> None:
  manifest_cluster = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp25_scheduler_semantics",
    "wp25_manifest_event_cluster_20260519.md",
  )
  manifest_cluster_zh = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp25_scheduler_semantics",
    "wp25_manifest_event_cluster_20260519.zh.md",
  )

  for stage in (
    "P0 ContentCompile",
    "P1 WorldSetup",
    "P2 TaskingIntent",
    "P3 CommandDelivery",
    "P4 PlatformControl",
    "P5 PhysicsStep",
    "P6 SenseTrackLink",
    "P7 FireControlLaunch",
    "P8 MunitionLifecycle",
    "P9 EffectsDamage",
    "P10 ObservationExport",
  ):
    assert f"semantic_stage: [{stage}]" in manifest_cluster
    assert f"semantic_stage: [{stage}]" in manifest_cluster_zh


def test_runtime_capabilities_trigger_stays_dormant_without_maintained_non_reference_profile() -> None:
  wp6 = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp6_backend_profile_policy",
    "backend_profile_policy_wp6_20260519.md",
  )
  wp6_zh = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp6_backend_profile_policy",
    "backend_profile_policy_wp6_20260519.zh.md",
  )
  wp7 = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp7_backend_capability_materialization",
    "backend_capability_materialization_wp7_20260519.md",
  )
  wp7_zh = _text(
    "docs",
    "task",
    "simulation_architecture",
    "wp7_backend_capability_materialization",
    "backend_capability_materialization_wp7_20260519.zh.md",
  )
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

  assert "non-reference backend profile is itself maintained" in wp6
  assert "non-reference backend profile 本身进入 maintained" in wp6_zh
  assert "at least one non-reference backend" in wp7
  assert "至少一个 non-reference backend profile" in wp7_zh
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
