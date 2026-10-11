from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp"


def test_world_batch_broadphase_uses_the_packed_radius_bound() -> None:
  source = RUNTIME.read_text(encoding="utf-8")

  assert "make_interaction_broadphase_config(std::size_t max_entities_per_world, double range_hint_m," in source
  assert "double max_entity_radius_m)" in source
  assert "config.max_entity_radius_m = std::max(0.0, max_entity_radius_m);" in source
  assert source.count("max_entity_radius_m = std::max(max_entity_radius_m, packed.bounding_radius_m);") == 2
  assert "config.max_entity_radius_m = 250.0;" not in source
