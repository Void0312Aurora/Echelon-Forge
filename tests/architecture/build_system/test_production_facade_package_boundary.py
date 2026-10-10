from __future__ import annotations

from zipfile import ZipFile

from tests.architecture.helpers import REPO_ROOT


CMAKE = REPO_ROOT / "CMakeLists.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"
PYTHON_MODULE = REPO_ROOT / "src" / "interfaces" / "python" / "python_module.cpp"
FACADE_BINDINGS = (
  REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime_facade_only.cpp"
)
GPU_FACADE_BINDINGS = (
  REPO_ROOT / "src" / "interfaces" / "python" / "bindings_gpu_facade_only.cpp"
)


def test_production_binding_options_fail_closed_to_facade_only() -> None:
  cmake = CMAKE.read_text(encoding="utf-8")
  pyproject = PYPROJECT.read_text(encoding="utf-8")
  module = PYTHON_MODULE.read_text(encoding="utf-8")
  facade_bindings = FACADE_BINDINGS.read_text(encoding="utf-8")
  gpu_facade_bindings = GPU_FACADE_BINDINGS.read_text(encoding="utf-8")

  assert 'option(EF_PRODUCTION_FACADE_ONLY "Build the production Python module with facade/contracts only" OFF)' in cmake
  assert 'option(EF_BUILD_DIAGNOSTICS_BINDINGS "Build the explicit opt-in ef_py_diagnostics raw binding module" OFF)' in cmake
  assert 'EF_PRODUCTION_FACADE_ONLY = "ON"' in pyproject
  assert 'EF_BUILD_DIAGNOSTICS_BINDINGS = "OFF"' in pyproject

  assert "list(FILTER EF_PYTHON_BINDING_SOURCES EXCLUDE REGEX" in cmake
  for raw_binding in (
    "bindings_core",
    "bindings_gpu",
    "bindings_runtime\\.cpp$",
    "bindings_runtime_engine\\.cpp$",
  ):
    assert raw_binding in cmake
  assert 'EXCLUDE REGEX "bindings_core|bindings_gpu|bindings_runtime\\.cpp$|bindings_runtime_engine\\.cpp$"' in cmake
  assert "bindings_episode.cpp" in cmake
  assert "bindings_episode_state_batch.cpp" in cmake

  assert "bind_runtime_facade_only(m);" in module
  assert "bind_core(m);" in module
  assert "bind_episode(m);" in module
  assert "bind_gpu_facade_only(m);" in module
  assert "bind_gpu(m);" in module
  assert "compute_world_batch_visual_observation_batch_numpy" in gpu_facade_bindings
  assert "compute_world_batch_visual_observation_batch_export" in gpu_facade_bindings
  assert "runtime/compatibility/runtime_facade_visual_observation.h" in gpu_facade_bindings
  assert "bind_runtime_facade(m);" in facade_bindings
  assert "nb::class_<WorldBatchRuntime" not in facade_bindings
  assert "nb::class_<SimulationKernel" not in facade_bindings
  assert "bind_runtime_engine" not in facade_bindings
  assert "add_library(ef_facade_backend SHARED" in cmake
  assert "src/runtime/compatibility/runtime_facade_visual_observation.cpp" in cmake
  assert "EF_FACADE_BACKEND_BUILD=1" in cmake
  assert "EF_FACADE_BACKEND_CONSUMER=1" in cmake
  production_link_block = cmake.split(
    "if (EF_PRODUCTION_FACADE_ONLY)\n    target_compile_definitions", 1
  )[1].split(
    "else()", 1
  )[0]
  production_link_block = "target_compile_definitions" + production_link_block
  assert "target_link_libraries(ef_py PRIVATE" in production_link_block
  assert "ef_facade_backend" in production_link_block
  assert "ef_gpu_experiments" not in production_link_block


def test_runtime_binding_modes_share_one_ordered_registration_spine() -> None:
  detail = _read(REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime_detail.h")
  diagnostic = _read(REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp")
  facade_only = _read(
    REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime_facade_only.cpp"
  )

  assert "inline void bind_runtime_shared_order(nb::module_ &m, bool include_raw_engine)" in detail
  assert "bind_runtime_engine(m);" in detail
  assert "bind_runtime_facade(m);" in detail
  assert "bind_runtime_shared_order(m, true);" in diagnostic
  assert "bind_runtime_shared_order(m, false);" in facade_only
  assert "bind_runtime_runtime(m);" not in diagnostic
  assert "bind_runtime_runtime(m);" not in facade_only


def test_diagnostics_binding_is_explicitly_separate_from_production_target() -> None:
  cmake = CMAKE.read_text(encoding="utf-8")
  diagnostics_block = cmake.split("if (EF_BUILD_DIAGNOSTICS_BINDINGS)", 1)[1].split(
    "endif()", 1
  )[0]

  assert "nanobind_add_module(ef_py_diagnostics" in diagnostics_block
  assert "${EF_PYTHON_DIAGNOSTICS_BINDING_SOURCES}" in diagnostics_block
  assert "EF_PYTHON_DIAGNOSTICS_MODULE=1" in diagnostics_block
  assert "target_link_libraries(ef_py_diagnostics PRIVATE ef_facade ef_core ef_gpu_experiments)" in diagnostics_block
  assert "install(TARGETS ef_py_diagnostics DESTINATION diagnostics)" in diagnostics_block

  production_block = cmake.split("nanobind_add_module(ef_py", 1)[1].split(
    "if (EF_BUILD_DIAGNOSTICS_BINDINGS)", 1
  )[0]
  assert "ef_py_diagnostics" not in production_block


def test_built_facade_only_wheel_has_no_raw_or_diagnostics_extension() -> None:
  wheel_dir = REPO_ROOT / "artifacts" / "p5c-wheel"
  wheels = sorted(wheel_dir.glob("cmo-*.whl"))
  if not wheels:
    return

  with ZipFile(wheels[-1]) as archive:
    names = archive.namelist()

  assert any(name.startswith("ef_py") and name.endswith(".pyd") for name in names)
  assert not any(name.startswith("ef_py_diagnostics") for name in names)
  assert not any("candidate_adapter" in name for name in names)


def test_production_package_defaults_to_facade_only_source_mapping() -> None:
  pyproject = PYPROJECT.read_text(encoding="utf-8")
  assert 'wheel.packages = ["python", "gym_envs"]' in pyproject
  assert '"rl/runtime/world_batch/candidate_adapter.py"' in pyproject
  assert '"python/rl/runtime/world_batch/candidate_adapter.py"' in pyproject
