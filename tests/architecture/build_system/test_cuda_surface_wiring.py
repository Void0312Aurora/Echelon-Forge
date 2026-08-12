from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from tests.architecture.helpers import REPO_ROOT
from tests.architecture.build_system.test_cmake_target_readiness import (
  _cmake_source,
  _find_commands,
  _normalize_source_path,
  _scoped_call_args,
  _strip_cmake_comments,
  _tokenize,
)


CUDA_RESIDENT_DIR = REPO_ROOT / "src" / "runtime" / "facade" / "internal" / "cuda_resident"
GPU_DIR = REPO_ROOT / "src" / "gpu"

# The resident backend's device sources are only compiled when CUDA experiments
# are enabled, and no CI lane enables them (no GPU runner, and nvcc is not
# preinstalled on the hosted images). That makes the whole surface invisible to
# the default gates: a device source could be deleted, renamed, or silently
# dropped from its CMake list and every green build would stay green.
#
# These gates are the toolkit-free half of that protection. They run on every
# machine, need no CUDA toolkit, and assert two things a CUDA-off build cannot:
#
#  1. the device sources on disk and the device sources CMake compiles remain
#     the same set (source-wiring gates below); and
#  2. each CUDA-only probe still *does* something -- its sources reference the
#     backend they link, and its entry point has a success path (probe-stub
#     gates below).
#
# Neither half can prove the code still compiles; only an actual CUDA-on build
# does that, which is why the opt-in `ci-cuda-compile` workflow exists and why
# the promotion program records a local CUDA-on build result at each iteration.
# Conversely, the compile lane cannot replace (2): a stub compiles cleanly.


# --- Device source wiring ----------------------------------------------------


def _wired_device_sources() -> set[str]:
  """Every ``.cu``/``.cuh`` path CMake adds to a source list."""
  source = _cmake_source()
  wired: set[str] = set()
  for command in ("list", "set"):
    for body in _find_commands(source, command):
      for token in _tokenize(body):
        if token.endswith(".cu") or token.endswith(".cuh"):
          wired.add(token)
  return wired


def _device_sources_on_disk() -> set[str]:
  return {
    path.relative_to(REPO_ROOT).as_posix()
    for path in (REPO_ROOT / "src").rglob("*.cu")
  }


def test_every_device_source_on_disk_is_compiled_by_cmake() -> None:
  """A ``.cu`` file that exists but is in no CMake list is dead weight that no
  build would ever reject."""
  orphaned = sorted(_device_sources_on_disk() - _wired_device_sources())
  assert not orphaned, (
    "device sources exist on disk but are wired into no CMake target: "
    f"{orphaned}. Add them to a source list or delete them; an unwired .cu "
    "file is invisible to every build."
  )


def test_every_device_source_cmake_names_exists_on_disk() -> None:
  """A CMake list naming a deleted ``.cu`` file only fails when CUDA is enabled,
  which no CI lane does -- so assert it here instead."""
  missing = sorted(
    token
    for token in _wired_device_sources()
    if token.endswith(".cu") and not (REPO_ROOT / token).is_file()
  )
  assert not missing, (
    f"CMake names device sources that do not exist: {missing}. This would only "
    "surface in a CUDA-on configure, which no CI lane runs."
  )


def test_resident_backend_device_source_count_is_pinned() -> None:
  """The resident backend's device surface is load-bearing evidence. CP-5 fused
  the six window-commit kernels into ``cuda_world_store_cuda_window_body.cu``,
  which makes the tracked v2 counter evidence a historical baseline for the
  pre-fusion topology; the v3 catalog owns the current one. A change in this
  file set still has to be deliberate, one reviewed iteration at a time."""
  present = sorted(path.name for path in CUDA_RESIDENT_DIR.glob("*.cu"))
  expected = [
    "cuda_world_store_cuda_barrier.cu",
    "cuda_world_store_cuda_control_preparation.cu",
    "cuda_world_store_cuda_observation.cu",
    "cuda_world_store_cuda_state_readback.cu",
    "cuda_world_store_cuda_storage.cu",
    "cuda_world_store_cuda_window.cu",
    "cuda_world_store_cuda_window_body.cu",
  ]
  assert present == expected, (
    "the resident backend device source set changed. The versioned kernel "
    "catalog and its capture evidence pin kernels compiled from these files; "
    "update the evidence and this pin together, in one reviewed iteration."
  )


def test_resident_backend_device_sources_are_cuda_gated() -> None:
  """The device sources must stay behind ``EF_ENABLE_CUDA_RESIDENT_BACKEND`` so
  a default build never requires a CUDA toolkit.

  After CP-2 the resident-backend device sources are gated on the new dedicated
  flag rather than the old umbrella ``EF_ENABLE_CUDA_EXPERIMENTS``.  The
  helpers in ``src/gpu/`` remain under ``EF_ENABLE_CUDA_EXPERIMENTS``."""
  source = _cmake_source()
  guard = "if (EF_ENABLE_CUDA_RESIDENT_BACKEND)"
  assert guard in source
  for name in (path.name for path in CUDA_RESIDENT_DIR.glob("*.cu")):
    index = source.find(name)
    assert index != -1, f"{name} is not referenced by CMakeLists.txt"
    preceding = source.rfind(guard, 0, index)
    assert preceding != -1, (
      f"{name} is added outside any EF_ENABLE_CUDA_RESIDENT_BACKEND guard, so a "
      "default build would need a CUDA toolkit"
    )


def test_gate_flags_an_unwired_device_source() -> None:
  """Negative case: the orphan check must actually reject a source that is on
  disk but absent from every CMake list."""
  wired = _wired_device_sources()
  disk = _device_sources_on_disk() | {"src/gpu/gpu_invented_runtime_cuda.cu"}
  assert sorted(disk - wired) == ["src/gpu/gpu_invented_runtime_cuda.cu"]


def test_gate_flags_a_cmake_named_device_source_that_is_gone() -> None:
  """Negative case: the missing-file check must reject a CMake entry naming a
  path that does not exist."""
  candidates = {"src/gpu/gpu_deleted_runtime_cuda.cu"}
  missing = sorted(
    token for token in candidates if not (REPO_ROOT / token).is_file()
  )
  assert missing == ["src/gpu/gpu_deleted_runtime_cuda.cu"]


def test_helper_and_resident_device_surfaces_stay_separate() -> None:
  """The two CUDA surfaces have different semantic standing: ``src/gpu`` holds
  optional accelerator helpers with CPU fallbacks, while the resident backend is
  a second world-step owner. Neither directory may absorb the other's sources."""
  helper_names = {path.name for path in GPU_DIR.glob("*.cu")}
  resident_names = {path.name for path in CUDA_RESIDENT_DIR.glob("*.cu")}
  assert not (helper_names & resident_names)
  assert all(name.startswith("gpu_") for name in helper_names)
  assert all(name.startswith("cuda_world_store_") for name in resident_names)


# --- Probe executability (the half a compile lane cannot cover) ---------------
# CP-4a retired the v1 resource capture probe by replacing its 335-line body
# with a stub that printed the retirement reason and returned EXIT_FAILURE
# (44e2b64e). The CMake target was left untouched: it still compiled the replay
# harness and linked both ef_cuda_resident_backend and nlohmann_json, while the
# stub source referenced none of them. That state builds and links cleanly, so a
# CUDA-on compile lane reports green on a probe that can no longer produce
# evidence. CP-4c then had to pay for the missing capture tool.
#
# These gates encode the two structural signatures of that state:
#   * a target links the resident backend but no source of that target names it;
#   * a target's entry point has no success return at all.
# Both are readable from the tree with no toolkit and no GPU.

BACKEND_LIBRARY = "ef_cuda_resident_backend"
BACKEND_SYMBOL = "CudaResidentBackend"

# Pinned so a probe cannot be deleted from CMakeLists.txt without review. Each
# entry is a CUDA-only executable that consumes the resident backend directly.
CUDA_PROBE_TARGETS = (
  "ef_cuda_resident_full_window_cuda_probe",
  "ef_cuda_resident_cr2_matrix_cuda_probe",
  "ef_cuda_resident_rb9_cuda_probe",
  "ef_cuda_resident_resource_probe",
)

_MAIN_PATTERN = re.compile(r"\bint\s+main\s*\(")
_SUCCESS_PATTERN = re.compile(r"\breturn\s+(?:0|EXIT_SUCCESS)\s*;")

SourceReader = Callable[[str], "str | None"]


def _executable_targets(text: str) -> dict[str, list[str]]:
  """Map every ``add_executable`` target to its source tokens."""
  targets: dict[str, list[str]] = {}
  for body in _find_commands(text, "add_executable"):
    tokens = _tokenize(body)
    if not tokens:
      continue
    rest = [t for t in tokens[1:] if t.upper() not in {"WIN32", "MACOSX_BUNDLE", "EXCLUDE_FROM_ALL"}]
    targets[tokens[0]] = rest
  return targets


def _repo_source_reader(root: Path) -> SourceReader:
  def read(rel_path: str) -> str | None:
    path = root / rel_path
    if not path.is_file():
      return None
    return path.read_text(encoding="utf-8", errors="replace")

  return read


def _probe_stub_violations(
  cmake_text: str, read_source: SourceReader, targets: tuple[str, ...]
) -> list[str]:
  """Return every way the CUDA probe targets look like retired stubs.

  An empty list means the gates are green. For each expected probe target:

  * (a) the target must exist in CMakeLists.txt at all;
  * (b) every source token it names must be readable (a probe naming a deleted
    file only fails a CUDA-on configure, which no CI lane runs);
  * (c) if the target links ``ef_cuda_resident_backend``, at least one of its
    sources must name ``CudaResidentBackend`` -- otherwise the link is vestigial
    and the probe drives nothing;
  * (d) exactly one source must define ``int main``, and that source must
    contain a success return. A probe whose only exit is a failure path is a
    retirement notice, not a probe.
  """
  text = _strip_cmake_comments(cmake_text)
  executables = _executable_targets(text)
  violations: list[str] = []

  for target in targets:
    sources = executables.get(target)
    if sources is None:
      violations.append(
        f"{target} is not defined by any add_executable call; a CUDA probe was "
        "removed without updating this pin"
      )
      continue

    bodies: dict[str, str] = {}
    for token in sources:
      rel_path = _normalize_source_path(token)
      body = read_source(rel_path)
      if body is None:
        violations.append(f"{target} names a source that does not exist: {rel_path}")
        continue
      bodies[rel_path] = body

    linked = [
      lib
      for call in _scoped_call_args(text, "target_link_libraries", target)
      for lib in call
    ]
    if BACKEND_LIBRARY in linked and not any(
      BACKEND_SYMBOL in body for body in bodies.values()
    ):
      violations.append(
        f"{target} links {BACKEND_LIBRARY} but no source of the target names "
        f"{BACKEND_SYMBOL}: the probe drives nothing and would still compile "
        "and link green"
      )

    entry_points = [
      rel_path for rel_path, body in bodies.items() if _MAIN_PATTERN.search(body)
    ]
    if len(entry_points) != 1:
      violations.append(
        f"{target} must have exactly one source defining int main "
        f"(found {sorted(entry_points)})"
      )
      continue
    entry = entry_points[0]
    if not _SUCCESS_PATTERN.search(bodies[entry]):
      violations.append(
        f"{entry} (entry point of {target}) has no success return: a probe "
        "whose only exit is a failure path is a retirement stub, which a "
        "compile lane reports green"
      )

  return violations


def test_cuda_probes_are_not_retired_stubs() -> None:
  """Every pinned CUDA-only probe still links a backend it actually drives and
  still has a success path.

  This is the executability half of CP-1. The compile lane covers "the wired
  sources still build"; this covers "the built probe still does its job", which
  is exactly what the v1 capture-probe retirement broke without turning
  anything red."""
  violations = _probe_stub_violations(
    _cmake_source(), _repo_source_reader(REPO_ROOT), CUDA_PROBE_TARGETS
  )
  assert not violations, "CUDA probe executability regressed:\n  " + "\n  ".join(
    violations
  )


# A minimal but structurally faithful probe wiring, used as the baseline for the
# negative cases below. It mirrors the real CMakeLists shape (a CUDA-gated
# add_executable that compiles a probe entry point plus the shared replay
# harness and links the resident backend) so mutations exercise the same parser.
_GOLDEN_PROBE_CMAKE = """\
if (EF_ENABLE_CUDA_RESIDENT_BACKEND)
    add_executable(ef_probe
        src/tools/experimental/cuda_resident/probe.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_probe PRIVATE
        ef_cuda_resident_backend
        nlohmann_json::nlohmann_json
    )
endif()
"""

_GOLDEN_PROBE_SOURCES = {
  "src/tools/experimental/cuda_resident/probe.cpp": """\
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

int main(int argc, char **argv) {
    try {
        runtime::cuda_resident::CudaResidentBackend backend;
        (void)backend;
        (void)argc;
        (void)argv;
        return 0;
    } catch (const std::exception &error) {
        return 1;
    }
}
""",
  "src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp": """\
namespace runtime::cuda_resident {
void replay_support() {}
} // namespace runtime::cuda_resident
""",
}

# Reproduced from 44e2b64e: the real retirement stub. It names neither the
# backend nor the JSON library its target still linked, and its only exit is a
# failure return.
_RETIREMENT_STUB = """\
#include <cstdlib>
#include <iostream>

#include "runtime/contracts/cuda_resident_resource_evidence_contract.h"

namespace {

namespace evidence = runtime::cuda_resident::resource_evidence;

static_assert(evidence::kCaptureProbeV1Retired);

} // namespace

int main() {
    std::cerr << "CUDA resident resource probe retired: "
              << evidence::kCaptureProbeV1RetirementReason << '\\n';
    return EXIT_FAILURE;
}
"""


def _dict_reader(sources: dict[str, str]) -> SourceReader:
  return lambda rel_path: sources.get(rel_path)


def test_probe_gate_baseline_golden_wiring_is_green() -> None:
  """Sanity anchor: the correct synthetic probe wiring must pass, so the red
  cases below prove the mutation was caught rather than a broken fixture."""
  assert (
    _probe_stub_violations(
      _GOLDEN_PROBE_CMAKE, _dict_reader(_GOLDEN_PROBE_SOURCES), ("ef_probe",)
    )
    == []
  )


def test_probe_gate_flags_the_historical_retirement_stub() -> None:
  """The regression this gate exists for: replacing a probe body with the real
  44e2b64e stub while leaving its CMake target intact must turn red on both
  counts -- the backend link becomes vestigial and the success path is gone."""
  sources = dict(_GOLDEN_PROBE_SOURCES)
  sources["src/tools/experimental/cuda_resident/probe.cpp"] = _RETIREMENT_STUB
  violations = _probe_stub_violations(
    _GOLDEN_PROBE_CMAKE, _dict_reader(sources), ("ef_probe",)
  )
  assert any("no source of the target names" in v for v in violations), violations
  assert any("no success return" in v for v in violations), violations


# --- CP-3: no non-SPI window-advance entry points on CudaResidentBackend ------
#
# CP-3 removes ``publish_stage`` and ``partial_sync_commit`` from the public
# interface of ``CudaResidentBackend``.  Before CP-3 those methods were
# reachable directly on the backend object; any caller could advance a window
# in a sequence that bypassed the SPI ``advance()`` entry point.  Removing them
# makes the equivalence claim ("advance() and the old manual sequence produce
# the same result") structurally enforced rather than incidental.
#
# The gate is intentionally header-level: it asserts the *declaration* is gone,
# not merely that callers were updated.  A declaration left in the header while
# callers are cleaned up would still allow future code to invoke the method.

_BACKEND_HEADER = (
  CUDA_RESIDENT_DIR / "cuda_resident_backend.h"
)

_NON_SPI_ADVANCE_METHODS = ("publish_stage", "partial_sync_commit")


def test_cuda_resident_backend_has_no_non_spi_window_advance_entry_points() -> None:
  """``CudaResidentBackend`` must not declare ``publish_stage`` or
  ``partial_sync_commit`` as public methods (CP-3).

  These were the non-SPI window-advance residue: callers could sequence inject
  → publish_stage → advance and bypass the equivalence contract.  After CP-3
  the only window-advance path is through the SPI ``advance()`` method, which
  internally calls ``CudaWorldStore::publish_stage`` when the window state
  requires it.

  The gate reads the header directly so a declaration snuck back in without a
  matching caller would still be caught."""
  assert _BACKEND_HEADER.is_file(), (
    f"cuda_resident_backend.h not found at {_BACKEND_HEADER}; "
    "update _BACKEND_HEADER if the file was moved"
  )
  source = _BACKEND_HEADER.read_text(encoding="utf-8")
  # Strip the testing namespace block so we only inspect the public class body.
  # The testing helpers legitimately operate on CudaWorldStore directly and are
  # not constrained by this gate.
  public_class_end = source.find("namespace testing {")
  assert public_class_end != -1, (
    "namespace testing { not found in cuda_resident_backend.h; "
    "the header structure changed — update this gate"
  )
  public_section = source[:public_class_end]
  for method in _NON_SPI_ADVANCE_METHODS:
    assert method not in public_section, (
      f"CudaResidentBackend still declares ``{method}`` in its public "
      f"interface (found in the pre-testing-namespace section of "
      f"cuda_resident_backend.h).  CP-3 retired these non-SPI window-advance "
      f"entry points; callers must go through the SPI ``advance()`` method."
    )


def test_probe_gate_flags_a_success_path_removed_on_its_own() -> None:
  """A narrower mutation: the probe still constructs the backend but its only
  exit becomes a failure return. The vestigial-link check stays green here, so
  this proves the entry-point check is independently load-bearing."""
  sources = dict(_GOLDEN_PROBE_SOURCES)
  sources["src/tools/experimental/cuda_resident/probe.cpp"] = (
    _GOLDEN_PROBE_SOURCES["src/tools/experimental/cuda_resident/probe.cpp"]
    .replace("return 0;", "return EXIT_FAILURE;")
  )
  violations = _probe_stub_violations(
    _GOLDEN_PROBE_CMAKE, _dict_reader(sources), ("ef_probe",)
  )
  assert [v for v in violations if "no success return" in v], violations
  assert not [v for v in violations if "names" in v and BACKEND_SYMBOL in v], violations


def test_probe_gate_flags_a_probe_deleted_from_cmake() -> None:
  """A pinned probe target removed from CMakeLists.txt must turn red rather
  than silently shrinking the CUDA surface under test."""
  violations = _probe_stub_violations(
    _GOLDEN_PROBE_CMAKE, _dict_reader(_GOLDEN_PROBE_SOURCES), ("ef_probe_gone",)
  )
  assert any("not defined by any add_executable" in v for v in violations), violations


def test_probe_gate_flags_a_named_source_that_does_not_exist() -> None:
  """A probe target naming a deleted source only fails a CUDA-on configure,
  which no CI lane runs -- so it must fail here."""
  cmake = _GOLDEN_PROBE_CMAKE.replace(
    "src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp",
    "src/tools/experimental/cuda_resident/deleted_session.cpp",
  )
  assert cmake != _GOLDEN_PROBE_CMAKE, "fixture mutation did not apply"
  violations = _probe_stub_violations(
    cmake, _dict_reader(_GOLDEN_PROBE_SOURCES), ("ef_probe",)
  )
  assert any("does not exist" in v for v in violations), violations


def test_probe_gate_tolerates_the_driving_source_being_a_sibling_tu() -> None:
  """Inverse case: the real probes split the entry point from the session TU
  that constructs the backend (``*_probe.cpp`` + ``*_session.cpp``). The
  vestigial-link check must accept the backend being named by a sibling source,
  not only by the file holding ``main``."""
  cmake = _GOLDEN_PROBE_CMAKE.replace(
    "src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp",
    "src/tools/experimental/cuda_resident/probe_session.cpp",
  )
  sources = {
    "src/tools/experimental/cuda_resident/probe.cpp": """\
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    return 0;
}
""",
    "src/tools/experimental/cuda_resident/probe_session.cpp": """\
#include "runtime/facade/internal/cuda_resident/cuda_resident_backend.h"

namespace {
void drive(runtime::cuda_resident::CudaResidentBackend &backend) { (void)backend; }
} // namespace
""",
  }
  assert _probe_stub_violations(cmake, _dict_reader(sources), ("ef_probe",)) == []


# --- CI surface/flag contract --------------------------------------------------

_SURFACE_FLAGS = {
  "ef_cuda_resident_backend": "-DEF_ENABLE_CUDA_RESIDENT_BACKEND=ON",
  "ef_gpu_experiments": "-DEF_ENABLE_CUDA_EXPERIMENTS=ON",
}


def _workflow_job_commands(workflow: str) -> list[tuple[str, list[str]]]:
  """Every ``run:`` block command as ``(job_id, tokens)``, in document order.

  Job identity and step order are preserved so a configure in another job or
  after a build step can never satisfy the binding. YAML full-line comments
  and inline shell comments are stripped, and backslash continuations are
  joined, so a flag only counts where it is an actual argument of an actual
  invocation -- never prose."""
  entries: list[tuple[str, str]] = []
  in_jobs = False
  job = ""
  in_run = False
  run_indent = 0
  for raw in workflow.splitlines():
    stripped = raw.strip()
    indent = len(raw) - len(raw.lstrip(" "))
    if not raw.startswith(" ") and stripped and not stripped.startswith("#"):
      in_jobs = stripped == "jobs:"
      in_run = False
      continue
    if in_jobs and indent == 2:
      match = re.match(r"([A-Za-z0-9_-]+):\s*(#.*)?$", stripped)
      if match:
        job = match.group(1)
        in_run = False
        continue
    if re.match(r"run:\s*[|>]?-?\s*$", stripped):
      in_run = True
      run_indent = indent
      continue
    if in_run:
      if stripped and indent <= run_indent:
        in_run = False
      elif stripped and not stripped.startswith("#"):
        entries.append((job, re.sub(r"\s#.*$", "", stripped).strip()))
  commands: list[tuple[str, list[str]]] = []
  current = ""
  current_job = ""
  for line_job, line in entries:
    if not current:
      current_job = line_job
    if line.endswith("\\"):
      current += line[:-1] + " "
      continue
    current += line
    if current.strip():
      commands.append((current_job, current.split()))
    current = ""
  if current.strip():
    commands.append((current_job, current.split()))
  return commands


def _genuine_configure_dir(tokens: list[str]) -> str | None:
  """The ``-B`` directory of a genuine CMake configure invocation.

  Genuine means: a ``cmake`` command that names a source tree (``-S``) and a
  build tree (``-B``) and is not a build or utility invocation. A
  ``cmake --version -B dir`` exits successfully but configures nothing, so it
  must never satisfy the binding."""
  if not tokens or tokens[0] != "cmake":
    return None
  utility = {"--build", "--version", "--help", "-E", "--open", "--install"}
  if any(token in utility for token in tokens):
    return None
  if not any(token == "-S" or (token.startswith("-S") and len(token) > 2) for token in tokens):
    return None
  for index, token in enumerate(tokens):
    if token == "-B" and index + 1 < len(tokens):
      return tokens[index + 1].rstrip("/")
    if token.startswith("-B") and len(token) > 2:
      return token[2:].rstrip("/")
  return None


def _build_invocation(tokens: list[str]) -> tuple[str, set[str]] | None:
  if not tokens or tokens[0] != "cmake" or "--build" not in tokens:
    return None
  index = tokens.index("--build")
  if index + 1 >= len(tokens):
    return None
  build_dir = tokens[index + 1].rstrip("/")
  targets: set[str] = set()
  if "--target" in tokens:
    for token in tokens[tokens.index("--target") + 1 :]:
      if token.startswith("-"):
        break
      targets.add(token)
  return build_dir, targets


def _cache_assignments(tokens: list[str]) -> dict[str, str]:
  """The ``-DNAME=VALUE`` assignments of one configure command, in order,
  with repeated assignments resolved by last-value precedence exactly as
  CMake resolves them."""
  assignments: dict[str, str] = {}
  for token in tokens:
    match = re.fullmatch(r"-D([A-Za-z0-9_]+)(?::[A-Za-z]+)?=(.*)", token)
    if match:
      assignments[match.group(1)] = match.group(2)
  return assignments


def _cuda_lane_flag_violations(workflow: str) -> list[str]:
  """Model the effective CMake cache per ``(job, build_dir)``: genuine
  configure invocations fold their ``-D`` assignments into the cache in
  document order (later assignments overwrite, unmentioned entries persist,
  exactly like CMake's cache), and each ``cmake --build`` checks the
  *effective value at that point*. Utility commands, other jobs, post-build
  configures, comments, and stale earlier values can never stand in for the
  cache state the build actually sees."""
  violations = []
  cache: dict[tuple[str, str], dict[str, str]] = {}
  for job, tokens in _workflow_job_commands(workflow):
    build = _build_invocation(tokens)
    if build is None:
      configure_dir = _genuine_configure_dir(tokens)
      if configure_dir is not None:
        cache.setdefault((job, configure_dir), {}).update(_cache_assignments(tokens))
      continue
    build_dir, targets = build
    for target in sorted(targets & set(_SURFACE_FLAGS)):
      flag = _SURFACE_FLAGS[target]
      name, expected = flag[2:].split("=", 1)
      state = cache.get((job, build_dir))
      if state is None:
        violations.append(
          f"the compile lane builds {target} in {build_dir} with no preceding "
          "same-job configure invocation for that build directory"
        )
      elif state.get(name) != expected:
        violations.append(
          f"the compile lane builds {target} but the effective {build_dir} "
          f"configure state does not set {name} to {expected}, so its .cu "
          "sources are silently excluded from the build"
        )
  return violations


def test_cuda_compile_lane_enables_the_flag_behind_every_surface_it_builds() -> None:
  """The compile lane's whole value is that the device sources actually pass
  through nvcc. Each CUDA surface hides its .cu sources behind its own CMake
  flag, so a lane that builds a surface's target without enabling the matching
  flag compiles only C++ fallbacks while claiming device coverage -- exactly
  what happened when ef_gpu_experiments was built without
  EF_ENABLE_CUDA_EXPERIMENTS. Only an actual CMake configure invocation can
  satisfy the flag requirement; comments and unrelated commands cannot."""
  workflow = (REPO_ROOT / ".github/workflows/ci-cuda-compile.yml").read_text(encoding="utf-8")
  assert _cuda_lane_flag_violations(workflow) == []
  # The real lane must actually build both surfaces; if a target disappears
  # from the lane entirely, that is its own regression.
  built: set[str] = set()
  for _job, tokens in _workflow_job_commands(workflow):
    build = _build_invocation(tokens)
    if build is not None:
      built.update(build[1])
  for target in _SURFACE_FLAGS:
    assert target in built, f"the compile lane no longer builds {target}"


def test_cuda_lane_flag_gate_rejects_prose_and_non_configure_carriers() -> None:
  """Mutation coverage from the review's convergence gates: with the real
  configure argument removed, none of these may satisfy the gate -- an
  ``echo`` step carrying the flag, a CMake utility command (with or without a
  ``-B`` token), a configure for an unrelated build directory, a same-
  directory configure in another job, a same-directory configure sequenced
  after the build, an inline shell comment, or a YAML comment."""
  workflow = (REPO_ROOT / ".github/workflows/ci-cuda-compile.yml").read_text(encoding="utf-8")
  flag = _SURFACE_FLAGS["ef_gpu_experiments"]

  def _flag_removed() -> str:
    mutated = workflow.replace(f"{flag} \\", "-DCMAKE_VERBOSE_MAKEFILE=ON \\")
    assert flag not in mutated
    return mutated

  same_job_carriers = {
    "echo step": "\n      - name: Prose step\n        run: |\n" + f"          echo {flag}\n",
    "cmake utility command": (
      "\n      - name: Utility\n        run: |\n" + f"          cmake --version {flag}\n"
    ),
    "cmake utility command with -B": (
      "\n      - name: Utility probe\n        run: |\n"
      + f"          cmake --version -B build-cuda {flag}\n"
    ),
    "unrelated configure": (
      "\n      - name: Other tree\n        run: |\n"
      + f"          cmake -S . -B build-other {flag}\n"
    ),
    "same-directory configure after the build": (
      "\n      - name: Late configure\n        run: |\n"
      + f"          cmake -S . -B build-cuda {flag}\n"
    ),
  }
  for label, carrier in same_job_carriers.items():
    mutated = _flag_removed() + carrier
    assert _cuda_lane_flag_violations(mutated), f"{label} satisfied the gate"

  other_job_configure = _flag_removed() + (
    "\n"
    "  other-job:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - name: Foreign configure\n"
    "        run: |\n"
    f"          cmake -S . -B build-cuda {flag}\n"
  )
  assert _cuda_lane_flag_violations(other_job_configure), (
    "a same-directory configure in another job satisfied the gate"
  )

  removed_with_inline_comment = _flag_removed().replace(
    "cmake -S . -B build-cuda -G Ninja \\",
    f"cmake -S . -B build-cuda -G Ninja \\  # was {flag}",
  )
  assert _cuda_lane_flag_violations(removed_with_inline_comment), (
    "an inline shell comment satisfied the gate"
  )

  yaml_commented = workflow.replace(flag, f"PLACEHOLDER_{flag[2:-3]}") + (
    "\n# note: configure once passed " + flag + "\n"
  )
  assert _cuda_lane_flag_violations(yaml_commented), "a YAML comment satisfied the gate"

  target_only_in_comment = (
    "jobs:\n"
    "  demo:\n"
    "    steps:\n"
    "      - name: Configure\n"
    "        run: |\n"
    "          # cmake once enabled -DEF_ENABLE_CUDA_EXPERIMENTS=ON here\n"
    "          cmake -S . -B build -DEF_ENABLE_CUDA_RESIDENT_BACKEND=ON\n"
    "      - name: Build\n"
    "        run: |\n"
    "          cmake --build build --target ef_gpu_experiments  # echo -DEF_ENABLE_CUDA_EXPERIMENTS=ON\n"
  )
  assert _cuda_lane_flag_violations(target_only_in_comment) == [
    "the compile lane builds ef_gpu_experiments but the effective build "
    "configure state does not set EF_ENABLE_CUDA_EXPERIMENTS to ON, so its .cu "
    "sources are silently excluded from the build"
  ]


def test_cuda_lane_flag_gate_models_the_effective_cache_state() -> None:
  """Sixth-round convergence gates: the flag check follows CMake's cache
  semantics, not token unions. A later same-tree reconfigure that flips the
  flag OFF must fail even though the earlier ON token exists; ON followed by
  OFF inside one configure command resolves to OFF and must fail; and -- the
  honest inverse -- a later reconfigure that does not mention the flag keeps
  the cached ON and must still pass."""
  workflow = (REPO_ROOT / ".github/workflows/ci-cuda-compile.yml").read_text(encoding="utf-8")
  flag = _SURFACE_FLAGS["ef_gpu_experiments"]
  name = flag[2:].split("=", 1)[0]
  later_off = workflow.replace(
    "      - name: Compile the device surfaces",
    "      - name: Reconfigure\n"
    "        run: |\n"
    f"          cmake -S . -B build-cuda -D{name}=OFF\n"
    "      - name: Compile the device surfaces",
    1,
  )
  assert _cuda_lane_flag_violations(later_off), (
    "a later same-tree OFF reconfigure did not trip the gate"
  )

  on_then_off = workflow.replace(flag, f"{flag} -D{name}=OFF", 1)
  assert _cuda_lane_flag_violations(on_then_off), (
    "ON followed by OFF in one configure command did not trip the gate"
  )

  cache_persists = workflow.replace(
    "      - name: Compile the device surfaces",
    "      - name: Reconfigure without the flag\n"
    "        run: |\n"
    "          cmake -S . -B build-cuda -DCMAKE_RULE_MESSAGES=OFF\n"
    "      - name: Compile the device surfaces",
    1,
  )
  assert _cuda_lane_flag_violations(cache_persists) == [], (
    "a flagless reconfigure wrongly cleared the cached ON"
  )
