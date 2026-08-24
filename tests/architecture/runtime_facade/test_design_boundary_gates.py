from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _strip_line_comment(line: str) -> str:
  return line.split("//", 1)[0].strip()


def test_maintained_facade_request_result_headers_do_not_include_engine_owners() -> None:
  headers = [
    *RUNTIME_CONTRACTS.glob("*.h"),
    RUNTIME_FACADE / "runtime_facade_types.h",
  ]
  violations: list[tuple[str, int, str]] = []

  for path in headers:
    for lineno, line in enumerate(_read(path).splitlines(), start=1):
      stripped = _strip_line_comment(line)
      if not stripped.startswith("#include"):
        continue
      if '"core/engine/' in stripped or "world_batch_runtime" in stripped:
        violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

  assert not violations, f"maintained request/result headers include engine owners: {violations}"


def test_facade_contract_and_types_headers_do_not_name_runtime_owner_types() -> None:
  headers = [
    *RUNTIME_CONTRACTS.glob("*.h"),
    RUNTIME_FACADE / "runtime_facade_types.h",
  ]
  forbidden = ("WorldBatchRuntime", "SimulationKernel")
  violations: list[tuple[str, int, str]] = []

  for path in headers:
    for lineno, line in enumerate(_read(path).splitlines(), start=1):
      stripped = _strip_line_comment(line)
      if any(token in stripped for token in forbidden):
        violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

  assert not violations, f"facade contract/type headers expose runtime owner types: {violations}"


def test_runtime_facade_header_owns_only_the_backend_interface() -> None:
  header = _read(RUNTIME_FACADE / "runtime_facade.h")

  assert '#include "core/engine/world_batch_runtime.h"' not in header
  assert "class IWorldBatchBackend;" in header
  assert "class WorldBatchRuntime;" not in header
  assert "runtime_compatibility_quarantine" not in header

  public_section = header.split("public:", 1)[1].split("private:", 1)[0]
  public_owner_lines = [
    _strip_line_comment(line)
    for line in public_section.splitlines()
    if "WorldBatchRuntime" in _strip_line_comment(line)
  ]
  assert public_owner_lines == []

  private_section = header.split("private:", 1)[1]
  assert "std::unique_ptr<IWorldBatchBackend> runtime_;" in private_section
  assert "std::unique_ptr<WorldBatchRuntime>" not in private_section


def test_world_batch_backend_seam_is_used_without_exposing_engine_or_gpu_owners() -> None:
  interface = _read(RUNTIME_FACADE / "internal/world_batch_backend.h")
  compatibility = _read(RUNTIME_FACADE / "internal/world_batch_compatibility_port.h")
  runtime = _read(REPO_ROOT / "src/core/engine/world_batch_runtime.h")
  cpu_backend = _read(RUNTIME_FACADE / "internal/flecs_cpu_backend.h")
  probe = _read(REPO_ROOT / "src/tests/test_world_batch_backend_contract.cpp")
  facade_source = _read(RUNTIME_FACADE / "runtime_facade.cpp")
  provider_source = _read(RUNTIME_FACADE / "internal/world_batch_backend_provider.cpp")

  assert "class IWorldBatchBackend" in interface
  for operation in (
    "configuration()",
    "configure(",
    "load_content(",
    "reset(",
    "setup(",
    "inject(",
    "evaluate(",
    "advance(",
    "export_state(",
    "diagnostics()",
  ):
    assert operation in interface
  assert "WorldBatchRuntime" not in interface
  assert "SimulationKernel" not in interface
  assert "WorldBatchVisualBindingCompatibilityScene" not in interface
  assert "bool use_gpu" not in interface
  assert "gpu::" not in interface
  assert "IEnvironmentModel" not in interface
  assert '#include "core/engine/' not in interface
  assert "bool use_gpu" in compatibility
  assert "WorldBatchVisualBindingCompatibilityScene" in compatibility
  assert "class WorldBatchRuntime : public IWorldBatchBackend" not in runtime
  assert "~WorldBatchRuntime() = default;" in runtime
  assert "class FlecsCpuBackend final : public IWorldBatchBackend" in cpu_backend
  assert "WorldBatchRuntime runtime_;" in cpu_backend
  assert "public WorldBatchRuntime" not in cpu_backend
  assert "FlecsCpuBackend" not in facade_source
  assert "std::make_unique<FlecsCpuBackend>" in provider_source
  assert '#include "runtime/facade/internal/world_batch_backend.h"' in probe
  assert "class IndependentBackendProbe final : public IWorldBatchBackend" in probe
  assert "world_batch_runtime.h" not in probe.lower()
  assert "gpu/" not in probe.lower()

  for request_marker, next_marker in (
    ("struct ResetRequest", "enum class SetupKind"),
    ("struct SetupRequest", "struct SetupResult"),
    ("struct InputBatch", "struct InputResult"),
    ("struct AdvanceRequest", "struct AdvanceResult"),
    ("struct EvaluationRequest", "struct EvaluationResult"),
    ("struct ExportRequest", "struct ExportResult"),
  ):
    section = interface.split(request_marker, 1)[1].split(next_marker, 1)[0]
    assert "std::vector<" not in section, f"{request_marker} must remain a non-owning view"

  normalized_interface = " ".join(interface.split())
  assert (
    "evaluate(const runtime::backend::EvaluationRequest &request) const = 0;"
    in normalized_interface
  )


def test_runtime_facade_docs_do_not_describe_raw_runtime_as_maintained_path() -> None:
  readme_en = _read(RUNTIME_FACADE / "README.md")
  readme_zh = _read(RUNTIME_FACADE / "README.zh.md")

  assert "Escape Hatch Retirement" in readme_en
  assert "no longer exposes a raw `WorldBatchRuntime` escape hatch" in readme_en
  assert "must use facade-level request/result APIs" in readme_en
  assert "不得重新引入 `RuntimeFacade.runtime_compatibility_quarantine()`" in readme_en
  assert "must not cache raw `WorldBatchRuntime`" in readme_en

  assert "逃逸口退休" in readme_zh
  assert "不再公开 raw `WorldBatchRuntime` 逃逸口" in readme_zh
  assert "维护前端必须使用 facade-level request/result API" in readme_zh
  assert "不得从 adapter 重新暴露 compatibility runtime" in readme_zh


def test_no_broad_direct_sim_ban_is_encoded_in_architecture_tests() -> None:
  current_file = Path(__file__).resolve()
  architecture_tests = "\n".join(
    _read(path)
    for path in sorted((REPO_ROOT / "tests" / "architecture").rglob("test_*.py"))
    if path.resolve() != current_file
  )

  broad_patterns = [
    r"sim\.\*",
    r"direct\s+sim\.\*",
    r"forbid(?:s|den)?\s+.*sim\.",
    r"ban(?:s|ned)?\s+.*sim\.",
  ]
  offenders = [
    pattern
    for pattern in broad_patterns
    if re.search(pattern, architecture_tests, flags=re.IGNORECASE)
  ]

  assert not offenders, f"broad direct sim.* ban should wait for allowlists: {offenders}"
