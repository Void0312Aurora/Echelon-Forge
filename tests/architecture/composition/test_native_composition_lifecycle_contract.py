from __future__ import annotations

from pathlib import Path
import re

from tests.architecture.helpers import REPO_ROOT


COMPOSITION = REPO_ROOT / "src/runtime/composition"
CMAKE = REPO_ROOT / "CMakeLists.txt"
LIFECYCLE_TEST = REPO_ROOT / "src/tests/test_composition_lifecycle.cpp"


def _text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_native_composition_public_surface_is_owner_local_and_host_neutral() -> None:
  expected = {
    "composition_error.h",
    "composition_identity.h",
    "composition_identity.cpp",
    "composition_json.h",
    "composition_json.cpp",
    "provider_catalog.h",
    "provider_catalog.cpp",
    "composition_runtime.h",
    "composition_runtime.cpp",
    "composition_validation.cpp",
  }
  assert expected <= {path.name for path in COMPOSITION.iterdir() if path.is_file()}

  public = "\n".join(
    _text(COMPOSITION / name)
    for name in (
      "composition_error.h",
      "composition_json.h",
      "provider_catalog.h",
      "composition_runtime.h",
    )
  ).lower()
  for forbidden in (
    "flecs",
    "nanobind",
    "node_api",
    "nlohmann",
    "core/engine",
    "models/",
  ):
    assert forbidden not in public

  implementation = "\n".join(
    _text(path).lower()
    for path in COMPOSITION.iterdir()
    if path.suffix in {".h", ".cpp"}
  )
  for forbidden in ("flecs", "nanobind", "node_api", "core/engine", "models/"):
    assert forbidden not in implementation


def test_native_composition_target_is_an_independent_link_unit() -> None:
  cmake = _text(CMAKE)
  library = cmake.split("add_library(ef_composition STATIC", 1)[1].split(
    "# --- Content Library", 1
  )[0]
  assert "src/runtime/composition" in cmake
  assert "nlohmann_json::nlohmann_json" in library
  for forbidden in ("ef_core", "ef_facade", "flecs::flecs", "nanobind"):
    assert forbidden not in library

  source_block = cmake.split("set(EF_COMPOSITION_SOURCES", 1)[1].split(")", 1)[0]
  sources = re.findall(r"src/[^\s]+\.(?:cpp|cc|cxx)", source_block)
  assert sources
  assert all(source.startswith("src/runtime/composition/") for source in sources)

  focused = cmake.split("add_executable(ef_composition_lifecycle_test", 1)[1].split(
    "# Focused target for CUDA-on", 1
  )[0]
  links = focused.split("target_link_libraries", 1)[1].split(")", 1)[0]
  assert "ef_composition" in links
  assert "doctest::doctest" in links
  for forbidden in ("ef_core", "ef_facade", "ef_cuda", "ef_gpu"):
    assert forbidden not in links


def test_lifecycle_api_freezes_transaction_scope_handle_and_effect_semantics() -> None:
  catalog = _text(COMPOSITION / "provider_catalog.h")
  runtime = _text(COMPOSITION / "composition_runtime.h")
  implementation = _text(COMPOSITION / "composition_runtime.cpp")
  for declaration in (
    "class ILifecycleEffect",
    "virtual CompositionStatus commit()",
    "virtual void rollback() noexcept",
    "virtual void dispose() noexcept",
    "supports_replacement_handover",
    "class ServiceHandle",
    "std::weak_ptr<detail::ServiceHandleControl>",
    "class ProviderCatalog",
    "CompositionStatus freeze()",
  ):
    assert declaration in catalog
  for declaration in (
    "validate_resolved_composition",
    "scope_generation",
    "requested_manifest_sha256",
    "resolved_manifest_sha256",
    "service_for",
    "rebuild_scope",
    "class CompositionKernel",
  ):
    assert declaration in runtime
  for behavior in (
    "release_records(candidates, provider_ids, true)",
    "active.store(false",
    "candidate_generations",
    "provider_order.rbegin()",
  ):
    assert behavior in implementation


def test_native_parser_is_closed_and_rejects_noncanonical_numbers() -> None:
  parser = _text(COMPOSITION / "composition_json.cpp")
  assert "exact_object" in parser
  assert "kErrorUnexpectedField" in parser
  assert "kErrorMissingField" in parser
  assert "is_number_float" in parser
  assert "kErrorNoncanonicalNumber" in parser
  assert "parse_resolved_composition_json" in parser
  assert "parse_simulation_composition_manifest_json" in parser


def test_runtime_error_codes_are_stable_and_task_labels_do_not_leak() -> None:
  errors = _text(COMPOSITION / "composition_error.h")
  codes = re.findall(r'"(runtime\.composition\.[a-z_]+)"', errors)
  assert len(codes) >= 12
  assert len(codes) == len(set(codes))
  production = "\n".join(
    _text(path)
    for path in COMPOSITION.iterdir()
    if path.suffix in {".h", ".cpp"}
  )
  for task_label in ("P1-B", "P2-A", "P2-B", "P3-A"):
    assert task_label not in production


def test_focused_cpp_suite_covers_failure_atomicity_and_stale_handles() -> None:
  source = _text(LIFECYCLE_TEST)
  for case in (
    "native JSON ingestion reproduces the frozen P1-B resolved fixture",
    "native validation rejects catalog and resolved-order mismatch before construction",
    "realization freezes typed services and disposes in reverse dependency order",
    "construction and effect failures roll back all staged providers",
    "scope rebuild is failure atomic and invalidates only replaced generations",
    "typed validation rejects stale identity invalid scopes and explicit self cycles",
    "failed provider cleanup destroys effects before instances",
    "lifecycle callbacks cannot reenter stop or rebuild",
    "replacement rebuild updates identity atomically and enforces handover",
  ):
    assert case in source
  assert "fail_next_construction" in source
  assert "fail_next_effect_commit" in source
  assert "CHECK_FALSE(world.valid())" in source
  assert "CHECK_FALSE(episode.valid())" in source
