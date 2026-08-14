from __future__ import annotations

import posixpath
import re
from tests.architecture.helpers import REPO_ROOT
from tests.architecture.build_system.test_cmake_target_readiness import (
  _cmake_source,
  _find_commands,
  _strip_cmake_comments,
  _tokenize,
)


CUDA_RESIDENT_DIR = REPO_ROOT / "src" / "runtime" / "facade" / "internal" / "cuda_resident"
GPU_DIR = REPO_ROOT / "src" / "gpu"

# The CUDA-resident backend and optional GPU helpers are excluded from default
# CUDA-off builds. These toolkit-free gates keep their device-source wiring and
# opt-in compile workflow explicit; the CUDA-on lane provides the actual compiler
# check. Runtime execution remains a separate GPU-host responsibility.


# --- Device source wiring ----------------------------------------------------


def _wired_device_sources() -> set[str]:
  """Every ``.cu``/``.cuh`` path CMake adds to a source list."""
  source = _strip_cmake_comments(_cmake_source())
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
  """Catch a deleted ``.cu`` source without waiting for the CUDA-on lane."""
  missing = sorted(
    token
    for token in _wired_device_sources()
    if token.endswith(".cu") and not (REPO_ROOT / token).is_file()
  )
  assert not missing, (
    f"CMake names device sources that do not exist: {missing}. This would only "
    "surface during a CUDA-on configure without this structural gate."
  )


def test_resident_backend_device_source_count_is_pinned() -> None:
  """Keep changes to the maintained backend's device surface deliberate."""
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
    "the resident backend device source set changed; update this maintained "
    "surface pin in the same reviewed change"
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
    inline = re.match(r"run:\s+(\S.*)$", stripped)
    if inline and not inline.group(1).startswith(("|", ">")):
      entries.append((job, re.sub(r"\s#.*$", "", inline.group(1)).strip()))
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


def _normalize_dir(value: str) -> str:
  """``./build-cuda``, ``build-cuda/`` and ``build-cuda`` are one tree."""
  return posixpath.normpath(value)


def _join_split_options(tokens: list[str]) -> list[str]:
  """CMake accepts ``-D NAME=VALUE`` split across two arguments; normalize to
  the joined spelling (same for ``-U``, ``-S``, ``-B``) so one vocabulary
  covers both documented forms."""
  joined: list[str] = []
  skip = False
  for index, token in enumerate(tokens):
    if skip:
      skip = False
      continue
    if token in {"-D", "-U", "-S", "-B"} and index + 1 < len(tokens):
      joined.append(token + tokens[index + 1])
      skip = True
    else:
      joined.append(token)
  return joined


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
  if not any(token.startswith("-S") and len(token) > 2 for token in tokens):
    return None
  for token in tokens:
    if token.startswith("-B") and len(token) > 2:
      return _normalize_dir(token[2:])
  return None


def _build_invocation(tokens: list[str]) -> tuple[str, set[str]] | None:
  if not tokens or tokens[0] != "cmake" or "--build" not in tokens:
    return None
  index = tokens.index("--build")
  if index + 1 >= len(tokens):
    return None
  build_dir = _normalize_dir(tokens[index + 1])
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
  """Fail-closed single-configure-per-build-tree invariant.

  Emulating CMake's full cache lifecycle (reconfigures, ``-U`` removals,
  ``--fresh`` resets) in a gate invites exactly the review's false-green
  boundary, so the gate demands auditable simplicity instead: each built tree
  has exactly one preceding same-job genuine configure invocation, that
  invocation carries no cache-mutating escape hatches (``-U``, ``--fresh``),
  and its ``-D`` assignments (joined or split form, last value wins) must set
  the surface flag to ON. Anything else -- a reconfigure of the same tree in
  any spelling, an unrecognized mutation form, a missing configure -- is a
  violation, never a silent pass."""
  violations = []
  configures: dict[tuple[str, str], list[list[str]]] = {}
  for job, raw_tokens in _workflow_job_commands(workflow):
    tokens = _join_split_options(raw_tokens)
    build = _build_invocation(tokens)
    if build is None:
      configure_dir = _genuine_configure_dir(tokens)
      if configure_dir is not None:
        configures.setdefault((job, configure_dir), []).append(tokens)
      continue
    build_dir, targets = build
    for target in sorted(targets & set(_SURFACE_FLAGS)):
      flag = _SURFACE_FLAGS[target]
      name, expected = flag[2:].split("=", 1)
      seen = configures.get((job, build_dir), [])
      if not seen:
        violations.append(
          f"the compile lane builds {target} in {build_dir} with no preceding "
          "same-job configure invocation for that build directory"
        )
        continue
      if len(seen) > 1:
        violations.append(
          f"the compile lane reconfigures {build_dir} more than once before "
          f"building {target}; the gate requires exactly one configure "
          "invocation per build tree so the effective cache state stays auditable"
        )
        continue
      configure = seen[0]
      if any(token.startswith("-U") or token == "--fresh" for token in configure):
        violations.append(
          f"the {build_dir} configure invocation carries a cache-mutating "
          "escape hatch (-U/--fresh), which the gate rejects fail-closed"
        )
        continue
      if _cache_assignments(configure).get(name) != expected:
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


def test_cuda_lane_flag_gate_fails_closed_on_every_cache_mutation_shape() -> None:
  """Sixth/seventh-round convergence gates. The gate is a fail-closed
  single-configure-per-build-tree invariant rather than a CMake cache
  emulator, so every cache-mutation shape the reviews probed must fail:
  a later same-tree OFF reconfigure (joined or split ``-D`` form, canonical
  or aliased directory spelling, block or inline ``run:``), ON followed by
  OFF inside the one configure command, ``-U`` removals, ``--fresh`` resets,
  and even a flagless reconfigure (auditability, not silence). The one
  accepted spelling variation is inside the single configure itself: the
  documented split ``-D NAME=ON`` form still counts as ON."""
  workflow = (REPO_ROOT / ".github/workflows/ci-cuda-compile.yml").read_text(encoding="utf-8")
  flag = _SURFACE_FLAGS["ef_gpu_experiments"]
  name = flag[2:].split("=", 1)[0]

  def _with_step_before_build(step_lines: str) -> str:
    return workflow.replace(
      "      - name: Compile the device surfaces",
      step_lines + "      - name: Compile the device surfaces",
      1,
    )

  reconfigures = {
    "joined -D OFF": f"          cmake -S . -B build-cuda -D{name}=OFF\n",
    "split -D OFF": f"          cmake -S . -B build-cuda -D {name}=OFF\n",
    "directory alias": f"          cmake -S . -B ./build-cuda -D{name}=OFF\n",
    "flagless reconfigure": "          cmake -S . -B build-cuda -DCMAKE_RULE_MESSAGES=OFF\n",
    "-U removal": f"          cmake -S . -B build-cuda -U {name}\n",
    "--fresh reset": "          cmake -S . -B build-cuda --fresh\n",
  }
  for label, command in reconfigures.items():
    mutated = _with_step_before_build("      - name: Reconfigure\n        run: |\n" + command)
    assert _cuda_lane_flag_violations(mutated), f"{label} reconfigure did not trip the gate"

  inline_reconfigure = _with_step_before_build(
    "      - name: Inline reconfigure\n"
    f"        run: cmake -S . -B build-cuda -D {name}=OFF\n"
  )
  assert _cuda_lane_flag_violations(inline_reconfigure), (
    "an inline run reconfigure did not trip the gate"
  )

  on_then_off = workflow.replace(flag, f"{flag} -D{name}=OFF", 1)
  assert _cuda_lane_flag_violations(on_then_off), (
    "ON followed by OFF in one configure command did not trip the gate"
  )

  escape_in_single_configure = workflow.replace(flag, f"{flag} -U OTHER_ENTRY", 1)
  assert _cuda_lane_flag_violations(escape_in_single_configure), (
    "-U inside the single configure did not trip the gate"
  )

  split_on = workflow.replace(flag, f"-D {name}=ON", 1)
  assert _cuda_lane_flag_violations(split_on) == [], (
    "the documented split -D NAME=ON spelling was wrongly rejected"
  )
