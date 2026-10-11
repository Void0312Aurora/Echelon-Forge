from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CUDA_SOURCES = tuple(
  REPO_ROOT / "src" / "gpu" / name
  for name in (
    "gpu_interaction_broadphase_runtime_cuda.cu",
    "gpu_flight_shaping_runtime_cuda.cu",
    "gpu_visual_runtime_cuda.cu",
    "gpu_execution_observation_runtime_cuda.cu",
  )
)


def test_cuda_helpers_allocate_replacements_before_releasing_cached_buffers() -> None:
  for path in CUDA_SOURCES:
    source = path.read_text(encoding="utf-8")
    assert "replace_device_buffer" in source
    assert "if (cudaMalloc(&replacement" in source
    assert "advertised_capacity = requested_capacity;" in source


def test_paired_cuda_cache_groups_are_committed_only_after_all_allocations_succeed() -> None:
  broadphase = (CUDA_SOURCES[0]).read_text(encoding="utf-8")
  visual = (CUDA_SOURCES[2]).read_text(encoding="utf-8")
  assert "replacement_queries" in broadphase
  assert "replacement_overflow" in broadphase
  assert "replacement_counts" in broadphase
  assert "replacement_objects" in visual
  assert "replacement_indices" in visual
  assert "replacement_keys" in visual
  assert "replacement_terrain_cls" in visual
  assert "replacement_output" in visual
