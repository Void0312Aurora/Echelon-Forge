"""P7-A native/Python/Cordis-produced host and batch parity evidence.

This probe keeps Cordis in the producer/control-plane role and proves that the
direct C++ host and the local ``ef_py`` binding execute the same admitted native
CPU-exact composition. Timing and sampled-RSS measurements are evaluated
separately from semantic identity under a frozen conservative regression budget.
"""

from __future__ import annotations

import argparse
import ctypes
from copy import deepcopy
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
  sys.path.insert(0, str(REPO_ROOT))
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
BUDGET_PATH = FIXTURES / "default_runtime_host_batch_parity_budget.v1.json"
EVIDENCE_PATH = FIXTURES / "default_runtime_host_batch_parity.windows_msvc.v1.json"
SEMANTIC_REFERENCE_PATH = FIXTURES / "default_runtime_host_batch_semantic_reference.v1.json"
CORDIS_PACKAGE = REPO_ROOT / "packages/cordis-runtime"
BUDGET_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_host_batch_parity_budget.v1.schema.json"
)
EVIDENCE_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_host_batch_parity.v1.schema.json"
)

SCHEMA_VERSION = "echelon_forge.runtime_host_batch_parity.v1"
EVIDENCE_VERSION = "1.0.0"
CANONICALIZATION = "echelon_forge.sorted_utf8_json.v1"
HASH_ALGORITHM = "sha256"
NODE_STATUS = "conditional_held_p6b_not_admitted"

WORKLOAD = {
  "semantic_world_count": 2,
  "semantic_steps": 3,
  "measurement_world_count": 32,
  "warmup_steps": 3,
  "measurement_steps": 20,
  "reset_iterations": 5,
  "worker_threads": 1,
  "seed_base": 42,
  "time_step_s": 0.05,
}

MEASURED_METRICS = (
  "cold_construct_ms",
  "warm_construct_ms",
  "setup_ms",
  "step_ms_per_world",
  "reset_ms_per_world",
  "teardown_ms",
  "sampled_peak_delta_bytes_per_world",
  "peak_rss_delta_bytes_per_world",
  "teardown_residual_bytes_per_world",
)

BUDGET = {
  "schema_version": "echelon_forge.runtime_host_batch_parity_budget.v1",
  "budget_id": "default_cpu_exact.host_batch.v1",
  "budget_version": "1.0.0",
  "profile_id": "builtin.default_compatibility",
  "profile_version": "1.0.0",
  "workload": WORKLOAD,
  "semantic": {
    "absolute_tolerance": 1e-12,
    "repeat_count": 2,
    "require_exact_composition_identity": True,
  },
  "absolute_limits": {
    "cold_construct_ms": 5000.0,
    "warm_construct_ms": 5000.0,
    "setup_ms": 5000.0,
    "step_ms_per_world": 5.0,
    "reset_ms_per_world": 5.0,
    "teardown_ms": 5000.0,
    "sampled_peak_delta_bytes_per_world": 67108864.0,
    "peak_rss_delta_bytes_per_world": 67108864.0,
    "teardown_residual_bytes_per_world": 4194304.0,
  },
  "python_vs_native_limits": {
    "ratio_max": {
      "cold_construct_ms": 8.0,
      "warm_construct_ms": 8.0,
      "setup_ms": 8.0,
      "step_ms_per_world": 10.0,
      "reset_ms_per_world": 10.0,
      "teardown_ms": 8.0,
      "sampled_peak_delta_bytes_per_world": 4.0,
      "peak_rss_delta_bytes_per_world": 4.0,
      "teardown_residual_bytes_per_world": 4.0,
    },
    "slack": {
      "cold_construct_ms": 1000.0,
      "warm_construct_ms": 1000.0,
      "setup_ms": 1000.0,
      "step_ms_per_world": 1.0,
      "reset_ms_per_world": 1.0,
      "teardown_ms": 1000.0,
      "sampled_peak_delta_bytes_per_world": 33554432.0,
      "peak_rss_delta_bytes_per_world": 33554432.0,
      "teardown_residual_bytes_per_world": 4194304.0,
    },
  },
  "node_row_policy": NODE_STATUS,
}


class ParityError(RuntimeError):
  pass


def _read(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _pretty(value: Any) -> str:
  return json.dumps(
    value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
  ) + "\n"


def _canonical(value: Any) -> str:
  return json.dumps(
    value,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
    allow_nan=False,
  )


def _sha256(value: Any) -> str:
  return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _seal(value: dict[str, Any]) -> dict[str, Any]:
  sealed = deepcopy(value)
  payload = {
    key: item
    for key, item in sealed.items()
    if key not in {"canonical_json", "evidence_sha256"}
  }
  sealed["canonical_json"] = _canonical(payload)
  sealed["evidence_sha256"] = hashlib.sha256(
    sealed["canonical_json"].encode("utf-8")
  ).hexdigest()
  return sealed


def build_semantic_reference(semantic: dict[str, Any]) -> dict[str, Any]:
  payload = {
    "schema_version": "echelon_forge.runtime_host_batch_semantic_reference.v1",
    "reference_version": "1.0.0",
    "profile_id": "builtin.default_compatibility",
    "profile_version": "1.0.0",
    "semantic_world_count": WORKLOAD["semantic_world_count"],
    "semantic_steps": WORKLOAD["semantic_steps"],
    "canonicalization": CANONICALIZATION,
    "hash_algorithm": HASH_ALGORITHM,
    "semantic": deepcopy(semantic),
  }
  canonical = _canonical(payload)
  return {
    **payload,
    "canonical_json": canonical,
    "semantic_reference_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
  }


def validate_semantic_reference(value: dict[str, Any]) -> None:
  expected_keys = {
    "schema_version",
    "reference_version",
    "profile_id",
    "profile_version",
    "semantic_world_count",
    "semantic_steps",
    "canonicalization",
    "hash_algorithm",
    "semantic",
    "canonical_json",
    "semantic_reference_sha256",
  }
  if set(value) != expected_keys:
    raise ParityError("P7-A semantic reference shape mismatch")
  expected_identity = {
    "schema_version": "echelon_forge.runtime_host_batch_semantic_reference.v1",
    "reference_version": "1.0.0",
    "profile_id": "builtin.default_compatibility",
    "profile_version": "1.0.0",
    "semantic_world_count": WORKLOAD["semantic_world_count"],
    "semantic_steps": WORKLOAD["semantic_steps"],
    "canonicalization": CANONICALIZATION,
    "hash_algorithm": HASH_ALGORITHM,
  }
  for key, expected in expected_identity.items():
    if value.get(key) != expected:
      raise ParityError(f"P7-A semantic reference identity mismatch: {key}")
  payload = {
    key: item
    for key, item in value.items()
    if key not in {"canonical_json", "semantic_reference_sha256"}
  }
  canonical = _canonical(payload)
  if value["canonical_json"] != canonical:
    raise ParityError("P7-A semantic reference canonical JSON mismatch")
  if value["semantic_reference_sha256"] != hashlib.sha256(
    canonical.encode("utf-8")
  ).hexdigest():
    raise ParityError("P7-A semantic reference SHA-256 mismatch")


def write_budget(path: Path = BUDGET_PATH) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(_pretty(BUDGET), encoding="utf-8", newline="\n")


def _validate_schemas(budget: dict[str, Any], evidence: dict[str, Any]) -> None:
  try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
  except ImportError as error:
    raise ParityError("P7-A schema validation requires jsonschema") from error

  budget_schema = _read(BUDGET_SCHEMA_PATH)
  evidence_schema = _read(EVIDENCE_SCHEMA_PATH)
  registry = Registry().with_resource(
    budget_schema["$id"], Resource.from_contents(budget_schema)
  )
  validators = (
    ("budget", Draft202012Validator(budget_schema), budget),
    ("evidence", Draft202012Validator(evidence_schema, registry=registry), evidence),
  )
  issues = []
  for label, validator, value in validators:
    for issue in validator.iter_errors(value):
      path = ".".join(str(item) for item in issue.absolute_path)
      issues.append(f"{label}:{path}:{issue.message}")
  if issues:
    raise ParityError("P7-A schema validation failed: " + "; ".join(sorted(issues)))


def current_rss_bytes() -> int:
  if os.name == "nt":
    class ProcessMemoryCountersEx(ctypes.Structure):
      _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
      ]

    counters = ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = ctypes.c_void_p
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
      ctypes.c_void_p,
      ctypes.POINTER(ProcessMemoryCountersEx),
      ctypes.c_ulong,
    ]
    get_process_memory_info.restype = ctypes.c_int
    ok = get_process_memory_info(
      get_current_process(), ctypes.byref(counters), ctypes.sizeof(counters)
    )
    return int(counters.WorkingSetSize) if ok else 0
  if sys.platform.startswith("linux"):
    try:
      resident_pages = int(Path("/proc/self/statm").read_text().split()[1])
      return resident_pages * int(os.sysconf("SC_PAGE_SIZE"))
    except (OSError, ValueError, IndexError):
      return 0
  if sys.platform == "darwin":
    try:
      result = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(os.getpid())],
        check=True,
        capture_output=True,
        text=True,
      )
      return int(result.stdout.strip()) * 1024
    except (OSError, subprocess.SubprocessError, ValueError):
      return 0
  return 0


def peak_rss_bytes() -> int:
  if os.name == "nt":
    class ProcessMemoryCountersEx(ctypes.Structure):
      _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
      ]

    counters = ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = ctypes.c_void_p
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
      ctypes.c_void_p,
      ctypes.POINTER(ProcessMemoryCountersEx),
      ctypes.c_ulong,
    ]
    get_process_memory_info.restype = ctypes.c_int
    ok = get_process_memory_info(
      get_current_process(), ctypes.byref(counters), ctypes.sizeof(counters)
    )
    return int(counters.PeakWorkingSetSize) if ok else 0
  if sys.platform.startswith("linux"):
    try:
      for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
          return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
      return 0
    return 0
  try:
    import resource

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)
  except (ImportError, ValueError):
    return 0


def trim_process_allocator() -> None:
  """Exclude free glibc arena retention from live teardown RSS samples."""
  if not sys.platform.startswith("linux"):
    return
  try:
    libc = ctypes.CDLL(None)
    malloc_trim = libc.malloc_trim
    malloc_trim.argtypes = [ctypes.c_size_t]
    malloc_trim.restype = ctypes.c_int
    malloc_trim(0)
  except (AttributeError, OSError):
    # Non-glibc Linux runtimes may not expose malloc_trim. Their allocator
    # behavior remains visible instead of being guessed or silently emulated.
    return


def _setup_request(ef_py: Any, world_count: int) -> Any:
  request = ef_py.BatchWorldSetupRequest()
  request.seeds = [WORKLOAD["seed_base"] + world for world in range(world_count)]
  request.time_steps = [WORKLOAD["time_step_s"]] * world_count
  spawns = []
  for world in range(world_count):
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = world
    spawn.side = ef_py.Side.Blue
    spawn.type_name = "Aircraft"
    spawn.entity_name = f"HostBatchParity{world}"
    spawn.is_agent = True
    spawn.x = 1000.0 + world * 100.0
    spawn.z = 1500.0
    spawn.vx = 200.0
    spawn.heading = 90.0
    spawns.append(spawn)
  request.spawn_requests = spawns
  return request


def _refs(ef_py: Any, entity_ids: list[int]) -> list[Any]:
  result = []
  for world, entity_id in enumerate(entity_ids):
    ref = ef_py.WorldEntityRef()
    ref.world_index = world
    ref.entity_id = entity_id
    result.append(ref)
  return result


def _observation(value: Any) -> dict[str, Any]:
  return {
    "sim_time": value.sim_time,
    "entity_id": value.id,
    "x": value.x,
    "y": value.y,
    "z": value.z,
    "vx": value.vx,
    "vy": value.vy,
    "vz": value.vz,
    "heading": value.heading,
    "pitch": value.pitch,
    "roll": value.roll,
    "speed": value.speed,
    "health": value.health,
  }


def _state_without_entity_ids(facade: Any, refs: list[Any]) -> list[dict[str, Any]]:
  result = [_observation(value) for value in facade.get_agent_observations_batch(refs)]
  for row in result:
    del row["entity_id"]
  return result


def _reset_cleared_entities(facade: Any, refs: list[Any]) -> bool:
  observations = facade.get_agent_observations_batch(refs)
  return all(
    value.sim_time == 0.0
    and value.x == 0.0
    and value.y == 0.0
    and value.z == 0.0
    and value.vx == 0.0
    and value.vy == 0.0
    and value.vz == 0.0
    and value.speed == 0.0
    and value.health == 0.0
    for value in observations
  )


def _composition(value: Any) -> dict[str, Any]:
  return {
    "runtime_request_sha256": value.runtime_request_sha256,
    "catalog_lock_sha256": value.catalog_lock_sha256,
    "profile_projection_sha256": value.profile_projection_sha256,
    "requested_manifest_sha256": value.requested_manifest_sha256,
    "resolved_manifest_sha256": value.resolved_manifest_sha256,
    "executable_graph_sha256": value.executable_graph_sha256,
    "evidence_sha256": value.evidence_sha256,
    "backend_provider_id": value.backend.provider_id,
    "backend_implementation_version": value.backend.implementation_version,
    "backend_profile_id": value.backend.backend_profile_id,
    "provider_count": len(value.provider_versions),
    "world_count": len(value.world_instances),
    "host_mode": value.host_mode,
    "binding_version": value.binding_version,
  }


def _pilot_actions(ef_py: Any, entity_ids: list[int]) -> tuple[list[Any], list[dict[str, Any]]]:
  assignments = []
  evidence = []
  for world, entity_id in enumerate(entity_ids):
    action = ef_py.PilotAction()
    action.stick_pitch = 0.2
    action.stick_roll = -0.1
    action.rudder = 0.05
    action.throttle = 0.75
    action.gear_handle = 0.0
    action.active = True
    assignment = ef_py.WorldPilotActionAssignment()
    assignment.world_index = world
    assignment.entity_id = entity_id
    assignment.action = action
    assignments.append(assignment)
    evidence.append(
      {
        "world_index": world,
        "entity_id": entity_id,
        "stick_pitch": 0.2,
        "stick_roll": -0.1,
        "rudder": 0.05,
        "throttle": 0.75,
        "gear_handle": 0.0,
        "active": True,
      }
    )
  return assignments, evidence


def _execution_outputs(ef_py: Any, facade: Any, refs: list[Any]) -> dict[str, Any]:
  states = []
  requests = []
  for ref in refs:
    state = ef_py.ExecutionEpisodeState()
    state.agent_id = ref.entity_id
    states.append(state)

    request = ef_py.WorldExecutionEpisodeStepRequest()
    request.world_index = ref.world_index
    request.entity_id = ref.entity_id
    request.config = ef_py.StepEvaluationBatchConfig()
    request.env_state.steps = 1
    request.env_state.max_steps = 10
    request.env_state.truth_x = 0.0
    request.env_state.truth_z = 1200.0
    request.env_state.truth_speed = 180.0
    request.env_state.has_safety = True
    request.env_state.safety.finite_state_valid = True
    request.env_state.safety.health = 100.0
    request.env_state.safety.survival_reward = 0.02
    request.env_state.has_waypoint = True
    request.env_state.waypoint.valid = True
    request.env_state.waypoint.waypoint_index = 0
    request.env_state.waypoint.waypoint_count = 1
    request.env_state.waypoint.dist_m = 50.0
    request.env_state.waypoint.waypoint_radius_m = 1200.0
    request.env_state.waypoint.has_prev_dist = True
    request.env_state.waypoint.prev_dist_m = 120.0
    request.env_state.waypoint.progress_weight = 0.1
    request.env_state.waypoint.distance_weight = -0.001
    request.env_state.waypoint.reached_bonus = 20.0
    requests.append(request)
  facade.prime_execution_episode_batch(refs, states)
  batch = ef_py.ExecutionBatchStepRequest()
  batch.step_requests = requests
  batch.include_agent_observations = False
  batch.include_instrument_states = False
  result = facade.step_execution_batch(batch)
  return {
    "rewards": list(result.rewards),
    "terminated": list(result.terminated),
    "truncated": list(result.truncated),
    "termination_reasons": list(result.termination_reasons),
    "reward_breakdown_jsons": list(result.reward_breakdown_jsons),
    "status_vectors": [list(value) for value in result.status_vectors],
    "step_info_valid_flags": list(result.step_info_valid_flags),
    "controller_state_changed_flags": list(result.controller_state_changed_flags),
  }


def _window_trace(window: Any) -> dict[str, Any]:
  return {
    "barriers": [
      {
        "sequence": value.sequence,
        "barrier_id": value.barrier_id,
        "node_id": value.node_id,
      }
      for value in window.barrier_trace
    ],
    "executed_nodes": [
      {
        "node_id": value.node_id,
        "execution_state": value.execution_state,
        "decision_reason": value.decision_reason,
        "trigger_source": value.trigger_source,
        "decision_barrier_id": value.decision_barrier_id,
        "source_snapshot_version": value.source_snapshot_version,
        "target_window_id": value.target_window_id,
        "visible_input_count": value.visible_input_count,
      }
      for value in window.executed_nodes
    ],
    "engagement": {
      "snapshot_version": window.engagement_packet.snapshot_version,
      "barrier_id": window.engagement_packet.barrier_id,
      "barrier_sequence": window.engagement_packet.barrier_sequence,
      "source_time_s": window.engagement_packet.source_time_s,
      "producer_node_id": window.engagement_packet.producer_node_id,
      "trace_ids": list(window.engagement_packet.trace_ids),
      "launch_event_count": len(window.engagement_packet.launch_events),
      "effects_event_count": len(window.engagement_packet.effects_events),
      "diagnostics_trace_count": len(window.engagement_packet.diagnostics_traces),
    },
  }


def _python_semantic_workload(ef_py: Any) -> dict[str, Any]:
  config = ef_py.RuntimeBatchConfig()
  config.world_count = WORKLOAD["semantic_world_count"]
  config.worker_threads = WORKLOAD["worker_threads"]
  facade = ef_py.RuntimeFacade(config)
  setup = facade.apply_world_setup(_setup_request(ef_py, WORKLOAD["semantic_world_count"]))
  entity_ids = list(setup.entity_ids)
  if len(entity_ids) != WORKLOAD["semantic_world_count"]:
    raise ParityError("Python semantic setup returned an unexpected entity count")
  refs = _refs(ef_py, entity_ids)
  initial = [_observation(value) for value in facade.get_agent_observations_batch(refs)]
  actions, action_evidence = _pilot_actions(ef_py, entity_ids)
  facade.set_pilot_actions_batch(actions)
  for _ in range(WORKLOAD["semantic_steps"]):
    facade.step_batch()
  final = [_observation(value) for value in facade.get_agent_observations_batch(refs)]
  execution_outputs = _execution_outputs(ef_py, facade, refs)
  composition = facade.export_composition_evidence()
  if not composition.available:
    raise ParityError(f"Python semantic composition evidence unavailable: {composition.error_code}")
  window_request = ef_py.RuntimeWindowRequest()
  window_request.window_id = "window:host-batch-parity"
  window_request.source_time_s = 5.0
  window_request.engagement_request.trace_ids = [facade.allocate_trace_id()]
  window = facade.run_window(window_request)
  replay = facade.build_maintained_replay_envelope(
    window, "run:host-batch-parity", "episode:host-batch-parity", 41
  )
  if not replay.admitted:
    raise ParityError(f"Python semantic replay envelope was not admitted: {replay.rejection_reason}")
  composition_ref = f"composition_evidence_sha256={composition.evidence.evidence_sha256}"
  evidence_refs = list(replay.evidence_refs)
  if composition_ref not in evidence_refs:
    raise ParityError("Python replay envelope omitted composition evidence")
  return {
    "composition": _composition(composition.evidence),
    "action_inputs": action_evidence,
    "initial_observations": initial,
    "final_observations": final,
    "execution_outputs": execution_outputs,
    "window_trace": _window_trace(window),
    "replay_comparison": {
      "admitted": bool(replay.admitted),
      "replay_envelope_id": replay.envelope.replay_envelope_id,
      "evidence_refs": evidence_refs,
      "composition_evidence_ref": composition_ref,
    },
  }


def _python_batch_measurement(ef_py: Any) -> dict[str, Any]:
  gc.collect()
  trim_process_allocator()
  rss_before = current_rss_bytes()
  peak_rss_before = peak_rss_bytes()
  config = ef_py.RuntimeBatchConfig()
  config.world_count = WORKLOAD["measurement_world_count"]
  config.worker_threads = WORKLOAD["worker_threads"]
  start = time.perf_counter()
  facade = ef_py.RuntimeFacade(config)
  cold_construct_ms = (time.perf_counter() - start) * 1000.0
  rss_after_construct = current_rss_bytes()

  start = time.perf_counter()
  setup_request = _setup_request(ef_py, WORKLOAD["measurement_world_count"])
  setup = facade.apply_world_setup(setup_request)
  setup_ms = (time.perf_counter() - start) * 1000.0
  if len(setup.entity_ids) != WORKLOAD["measurement_world_count"]:
    raise ParityError("Python batch setup returned an unexpected entity count")
  rss_after_setup = current_rss_bytes()

  for _ in range(WORKLOAD["warmup_steps"]):
    facade.step_batch()
  start = time.perf_counter()
  for _ in range(WORKLOAD["measurement_steps"]):
    facade.step_batch()
  step_total_ms = (time.perf_counter() - start) * 1000.0
  rss_after_steps = current_rss_bytes()

  reset_refs = _refs(ef_py, list(setup.entity_ids))
  representative_reset_state = _state_without_entity_ids(facade, reset_refs)
  reset_total_ms = 0.0
  for iteration in range(WORKLOAD["reset_iterations"]):
    if iteration:
      setup = facade.apply_world_setup(setup_request)
      if len(setup.entity_ids) != WORKLOAD["measurement_world_count"]:
        raise ParityError("Python repeated reset setup returned an unexpected entity count")
      reset_refs = _refs(ef_py, list(setup.entity_ids))
      for _ in range(WORKLOAD["warmup_steps"] + WORKLOAD["measurement_steps"]):
        facade.step_batch()
      if _state_without_entity_ids(facade, reset_refs) != representative_reset_state:
        raise ParityError("Python repeated reset did not receive the representative workload")
    start = time.perf_counter()
    facade.reset_batch()
    reset_total_ms += (time.perf_counter() - start) * 1000.0
    if not _reset_cleared_entities(facade, reset_refs):
      raise ParityError("Python reset did not clear the representative workload")
  rss_after_resets = current_rss_bytes()

  start = time.perf_counter()
  del facade
  gc.collect()
  teardown_ms = (time.perf_counter() - start) * 1000.0
  trim_process_allocator()
  rss_after_teardown = current_rss_bytes()
  rss_samples = (
    rss_before,
    rss_after_construct,
    rss_after_setup,
    rss_after_steps,
    rss_after_resets,
    rss_after_teardown,
  )
  if any(sample <= 0 for sample in rss_samples):
    raise ParityError("Python RSS measurement is unavailable")
  start = time.perf_counter()
  warm_facade = ef_py.RuntimeFacade(config)
  warm_construct_ms = (time.perf_counter() - start) * 1000.0
  del warm_facade
  gc.collect()
  peak_rss_after = peak_rss_bytes()
  if peak_rss_before <= 0 or peak_rss_after <= 0 or peak_rss_after < peak_rss_before:
    raise ParityError("Python peak RSS measurement is unavailable")
  sampled_peak_rss = max(
    rss_before, rss_after_construct, rss_after_setup, rss_after_steps, rss_after_resets
  )
  sampled_peak_delta = max(0, sampled_peak_rss - rss_before)
  peak_rss_delta = peak_rss_after - peak_rss_before
  teardown_residual = max(0, rss_after_teardown - rss_before)
  return {
    "cold_construct_ms": cold_construct_ms,
    "warm_construct_ms": warm_construct_ms,
    "setup_ms": setup_ms,
    "step_ms_per_batch": step_total_ms / WORKLOAD["measurement_steps"],
    "step_ms_per_world": step_total_ms
    / (WORKLOAD["measurement_steps"] * WORKLOAD["measurement_world_count"]),
    "reset_ms_per_batch": reset_total_ms / WORKLOAD["reset_iterations"],
    "reset_ms_per_world": reset_total_ms
    / (WORKLOAD["reset_iterations"] * WORKLOAD["measurement_world_count"]),
    "teardown_ms": teardown_ms,
    "rss_before_bytes": rss_before,
    "rss_after_construct_bytes": rss_after_construct,
    "rss_after_setup_bytes": rss_after_setup,
    "rss_after_steps_bytes": rss_after_steps,
    "rss_after_resets_bytes": rss_after_resets,
    "rss_after_teardown_bytes": rss_after_teardown,
    "sampled_peak_rss_bytes": sampled_peak_rss,
    "sampled_peak_delta_bytes": sampled_peak_delta,
    "sampled_peak_delta_bytes_per_world": sampled_peak_delta
    / WORKLOAD["measurement_world_count"],
    "peak_rss_before_bytes": peak_rss_before,
    "peak_rss_after_bytes": peak_rss_after,
    "peak_rss_delta_bytes": peak_rss_delta,
    "peak_rss_delta_bytes_per_world": peak_rss_delta
    / WORKLOAD["measurement_world_count"],
    "teardown_residual_bytes": teardown_residual,
    "teardown_residual_bytes_per_world": teardown_residual
    / WORKLOAD["measurement_world_count"],
  }


def capture_python_host(native: dict[str, Any]) -> dict[str, Any]:
  from python.runtime_bootstrap import configure_sim_log_level

  configure_sim_log_level("warn")
  import ef_py

  metrics = _python_batch_measurement(ef_py)
  first = _python_semantic_workload(ef_py)
  second = _python_semantic_workload(ef_py)
  if first != second:
    raise ParityError("Python semantic workload is not repeat-exact")
  return {
    "host_id": "python_nanobind",
    "host_kind": "python_binding",
    "execution_owner": "native_cpp",
    "caller_attestation": "ef_py_local_build",
    "environment": {
      "platform": native["environment"]["platform"],
      "runtime": f"python.{platform.python_version()}",
      "build_mode": native["environment"]["build_mode"],
      "logical_cpu_count": native["environment"]["logical_cpu_count"],
    },
    "semantic": first,
    "metrics": metrics,
  }


def capture_native_host(binary: Path, output: Path) -> dict[str, Any]:
  env = os.environ.copy()
  env["EF_P7_PARITY_REPORT"] = str(output)
  result = subprocess.run(
    [str(binary), "--test-case=P7-A default CPU-exact native host and batch parity probe"],
    cwd=REPO_ROOT,
    env=env,
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != 0 or not output.is_file():
    raise ParityError(
      "native P7-A probe failed\n" + result.stdout[-2000:] + "\n" + result.stderr[-2000:]
    )
  probe = _read(output)
  if probe.get("workload") != WORKLOAD:
    raise ParityError("native P7-A workload does not match the frozen budget")
  if probe.get("runtime_owner", {}).get("node_host_status") != NODE_STATUS:
    raise ParityError("native P7-A probe widened the held Node-host boundary")
  return {
    "host_id": "native_cpp_direct",
    "host_kind": "native_direct",
    "execution_owner": "native_cpp",
    "caller_attestation": "direct_executable",
    "environment": {
      "platform": probe["environment"]["platform"],
      "runtime": probe["environment"]["compiler"],
      "build_mode": probe["environment"]["build_mode"],
      "logical_cpu_count": probe["environment"]["logical_cpu_count"],
    },
    "semantic": probe["semantic"],
    "metrics": probe["metrics"],
  }


def capture_cordis_producer(
  node: str, output: Path, conformance_binary: Path
) -> dict[str, Any]:
  result = subprocess.run(
    [node, "src/cli.mjs", "produce", "--out", str(output)],
    cwd=CORDIS_PACKAGE,
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != 0:
    raise ParityError("Cordis producer failed\n" + result.stdout + "\n" + result.stderr)
  metadata = _read(output / "producer_metadata.json")
  provenance = _read(output / "runtime_package_provenance.v1.json")
  request = _read(output / "runtime_composition_request.v1.json")
  lock = _read(output / "admitted_catalog_lock.v1.json")
  projection = _read(output / "runtime_profile_projection.v1.json")
  requested_manifest = _read(output / "default_compatibility_manifest.requested.json")
  resolved_manifest = _read(output / "default_compatibility_manifest.resolved.json")
  if provenance["runtime_artifacts"] != {
    "request_sha256": metadata["request_sha256"],
    "lock_sha256": metadata["lock_sha256"],
    "profile_projection_sha256": metadata["profile_projection_sha256"],
  }:
    raise ParityError("Cordis provenance/runtime-artifact join is inconsistent")
  if _sha256(request) != metadata["request_sha256"]:
    raise ParityError("Cordis request identity is inconsistent")
  if lock["lock_sha256"] != metadata["lock_sha256"]:
    raise ParityError("Cordis lock identity is inconsistent")
  if projection["projection_sha256"] != metadata["profile_projection_sha256"]:
    raise ParityError("Cordis profile projection identity is inconsistent")
  requested_manifest_sha256 = _sha256(requested_manifest)
  resolved_manifest_sha256 = _sha256(
    {
      key: value
      for key, value in resolved_manifest.items()
      if key != "resolved_manifest_sha256"
    }
  )
  if requested_manifest_sha256 != resolved_manifest["requested_manifest_sha256"]:
    raise ParityError("Cordis requested manifest identity is inconsistent")
  if resolved_manifest_sha256 != resolved_manifest["resolved_manifest_sha256"]:
    raise ParityError("Cordis resolved manifest identity is inconsistent")
  conformance = subprocess.run(
    [
      str(conformance_binary),
      str(output / "runtime_composition_request.v1.json"),
      str(output / "admitted_catalog_lock.v1.json"),
      str(output / "owner_authority_registry.v1.json"),
      str(output / "default_compatibility_manifest.requested.json"),
      str(output / "default_compatibility_manifest.resolved.json"),
      str(output / "runtime_profile_projection.v1.json"),
    ],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  if conformance.returncode != 0 or (
    "native projection and low-level manifest conformance passed" not in conformance.stdout
  ):
    raise ParityError(
      "Cordis-produced artifacts failed native admission\n"
      + conformance.stdout
      + "\n"
      + conformance.stderr
    )
  return {
    "producer_id": "cordis",
    "package_name": provenance["producer"]["package_name"],
    "package_version": provenance["producer"]["package_version"],
    "cordis_version": metadata["cordis_version"],
    "runtime_package_id": metadata["runtime_package_id"],
    "runtime_package_version": metadata["runtime_package_version"],
    "request_sha256": metadata["request_sha256"],
    "lock_sha256": metadata["lock_sha256"],
    "profile_projection_sha256": metadata["profile_projection_sha256"],
    "requested_manifest_sha256": requested_manifest_sha256,
    "resolved_manifest_sha256": resolved_manifest_sha256,
    "package_provenance_sha256": metadata["runtime_package_provenance_sha256"],
    "dependency_graph_sha256": metadata["runtime_package_dependency_graph_sha256"],
    "native_admission_status": "validated",
  }


def expected_producer_identity() -> dict[str, Any]:
  request = _read(FIXTURES / "default_runtime_composition_request.v1.json")
  lock = _read(FIXTURES / "default_admitted_catalog_lock.v1.json")
  projection = _read(FIXTURES / "default_runtime_profile_projection.v1.json")
  requested_manifest = _read(FIXTURES / "default_compatibility_manifest.requested.json")
  resolved_manifest = _read(FIXTURES / "default_compatibility_manifest.resolved.json")
  provenance = _read(FIXTURES / "default_runtime_package_provenance.v1.json")
  return {
    "producer_id": "cordis",
    "package_name": provenance["producer"]["package_name"],
    "package_version": provenance["producer"]["package_version"],
    "cordis_version": provenance["producer"]["cordis_version"],
    "runtime_package_id": provenance["package"]["package_id"],
    "runtime_package_version": provenance["package"]["package_version"],
    "request_sha256": _sha256(request),
    "lock_sha256": lock["lock_sha256"],
    "profile_projection_sha256": projection["projection_sha256"],
    "requested_manifest_sha256": _sha256(requested_manifest),
    "resolved_manifest_sha256": _sha256(
      {
        key: value
        for key, value in resolved_manifest.items()
        if key != "resolved_manifest_sha256"
      }
    ),
    "package_provenance_sha256": provenance["provenance_sha256"],
    "dependency_graph_sha256": provenance["dependency_resolution"]["graph_sha256"],
    "native_admission_status": "validated",
  }


def _semantic_mismatches(expected: Any, actual: Any, path: str, tolerance: float) -> list[str]:
  if isinstance(expected, dict) and isinstance(actual, dict):
    if set(expected) != set(actual):
      return [path]
    result: list[str] = []
    for key in sorted(expected):
      result.extend(_semantic_mismatches(expected[key], actual[key], f"{path}.{key}", tolerance))
    return result
  if isinstance(expected, list) and isinstance(actual, list):
    if len(expected) != len(actual):
      return [path]
    result = []
    for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=True)):
      result.extend(
        _semantic_mismatches(expected_item, actual_item, f"{path}[{index}]", tolerance)
      )
    return result
  if isinstance(expected, bool) or isinstance(actual, bool):
    return [] if expected is actual else [path]
  if isinstance(expected, int) or isinstance(actual, int):
    return [] if type(expected) is int and type(actual) is int and expected == actual else [path]
  if isinstance(expected, float) and isinstance(actual, float):
    return [] if abs(float(expected) - float(actual)) <= tolerance else [path]
  return [] if expected == actual else [path]


def validate_metric_consistency(host: dict[str, Any]) -> None:
  metrics = host["metrics"]
  world_count = WORKLOAD["measurement_world_count"]
  duration_metrics = (
    "cold_construct_ms",
    "warm_construct_ms",
    "setup_ms",
    "step_ms_per_batch",
    "step_ms_per_world",
    "reset_ms_per_batch",
    "reset_ms_per_world",
    "teardown_ms",
  )
  if any(
    not math.isfinite(float(metrics[name])) or float(metrics[name]) <= 0.0
    for name in duration_metrics
  ):
    raise ParityError(f"P7-A duration measurement is unavailable for {host['host_id']}")
  current_rss_names = (
    "rss_before_bytes",
    "rss_after_construct_bytes",
    "rss_after_setup_bytes",
    "rss_after_steps_bytes",
    "rss_after_resets_bytes",
    "rss_after_teardown_bytes",
    "sampled_peak_rss_bytes",
    "peak_rss_before_bytes",
    "peak_rss_after_bytes",
  )
  if any(int(metrics[name]) <= 0 for name in current_rss_names):
    raise ParityError(f"P7-A RSS measurement is unavailable for {host['host_id']}")

  def require_close(name: str, actual: float, expected: float) -> None:
    if not math.isfinite(actual) or not math.isclose(
      actual, expected, rel_tol=1e-12, abs_tol=1e-9
    ):
      raise ParityError(f"P7-A metric derivation mismatch for {host['host_id']}: {name}")

  require_close(
    "step_ms_per_world",
    float(metrics["step_ms_per_world"]),
    float(metrics["step_ms_per_batch"]) / world_count,
  )
  require_close(
    "reset_ms_per_world",
    float(metrics["reset_ms_per_world"]),
    float(metrics["reset_ms_per_batch"]) / world_count,
  )
  sampled_peak = max(
    int(metrics["rss_before_bytes"]),
    int(metrics["rss_after_construct_bytes"]),
    int(metrics["rss_after_setup_bytes"]),
    int(metrics["rss_after_steps_bytes"]),
    int(metrics["rss_after_resets_bytes"]),
  )
  current_rss_samples = (
    int(metrics["rss_before_bytes"]),
    int(metrics["rss_after_construct_bytes"]),
    int(metrics["rss_after_setup_bytes"]),
    int(metrics["rss_after_steps_bytes"]),
    int(metrics["rss_after_resets_bytes"]),
    int(metrics["rss_after_teardown_bytes"]),
  )
  peak_before = int(metrics["peak_rss_before_bytes"])
  peak_after = int(metrics["peak_rss_after_bytes"])
  if peak_before < current_rss_samples[0] or peak_after < peak_before or peak_after < max(
    current_rss_samples
  ):
    raise ParityError(f"P7-A peak RSS does not dominate current RSS for {host['host_id']}")
  sampled_delta = max(0, sampled_peak - int(metrics["rss_before_bytes"]))
  peak_delta = int(metrics["peak_rss_after_bytes"]) - int(metrics["peak_rss_before_bytes"])
  teardown_residual = max(
    0, int(metrics["rss_after_teardown_bytes"]) - int(metrics["rss_before_bytes"])
  )
  exact_derivations = {
    "sampled_peak_rss_bytes": sampled_peak,
    "sampled_peak_delta_bytes": sampled_delta,
    "peak_rss_delta_bytes": peak_delta,
    "teardown_residual_bytes": teardown_residual,
  }
  for name, expected in exact_derivations.items():
    if int(metrics[name]) != expected:
      raise ParityError(f"P7-A metric derivation mismatch for {host['host_id']}: {name}")
  require_close(
    "sampled_peak_delta_bytes_per_world",
    float(metrics["sampled_peak_delta_bytes_per_world"]),
    sampled_delta / world_count,
  )
  require_close(
    "peak_rss_delta_bytes_per_world",
    float(metrics["peak_rss_delta_bytes_per_world"]),
    peak_delta / world_count,
  )
  require_close(
    "teardown_residual_bytes_per_world",
    float(metrics["teardown_residual_bytes_per_world"]),
    teardown_residual / world_count,
  )


def evaluate_budget(
  native: dict[str, Any], python_host: dict[str, Any], budget: dict[str, Any]
) -> dict[str, Any]:
  checks: list[dict[str, Any]] = []
  for host in (native, python_host):
    for metric in MEASURED_METRICS:
      observed = float(host["metrics"][metric])
      limit = float(budget["absolute_limits"][metric])
      checks.append(
        {
          "host_id": host["host_id"],
          "metric": metric,
          "mode": "absolute",
          "observed": observed,
          "limit": limit,
          "passed": observed <= limit,
        }
      )
  for metric in MEASURED_METRICS:
    observed = float(python_host["metrics"][metric])
    limit = (
      float(native["metrics"][metric])
      * float(budget["python_vs_native_limits"]["ratio_max"][metric])
      + float(budget["python_vs_native_limits"]["slack"][metric])
    )
    checks.append(
      {
        "host_id": python_host["host_id"],
        "metric": metric,
        "mode": "python_vs_native",
        "observed": observed,
        "limit": limit,
        "passed": observed <= limit,
      }
    )
  failed = [check for check in checks if not check["passed"]]
  if failed:
    raise ParityError(f"P7-A batch budget failed: {failed}")
  return {"status": "pass", "checks": checks}


def build_evidence(binary: Path, node: str) -> dict[str, Any]:
  budget = _read(BUDGET_PATH)
  if budget != BUDGET:
    raise ParityError("P7-A budget fixture is stale; run generate-budget")
  with tempfile.TemporaryDirectory(prefix="ef-p7-parity-") as temporary:
    root = Path(temporary)
    native = capture_native_host(binary, root / "native.json")
    python_host = capture_python_host(native)
    suffix = ".exe" if os.name == "nt" else ""
    conformance_binary = binary.parent / f"ef_cordis_runtime_conformance_test{suffix}"
    if not conformance_binary.is_file():
      raise ParityError(f"native Cordis conformance binary is missing: {conformance_binary}")
    producer = capture_cordis_producer(node, root / "cordis", conformance_binary)
    if producer != expected_producer_identity():
      raise ParityError("live Cordis producer identity drifted from the admitted P6-A fixtures")

  tolerance = float(budget["semantic"]["absolute_tolerance"])
  mismatches = _semantic_mismatches(
    native["semantic"], python_host["semantic"], "$.hosts.semantic", tolerance
  )
  if mismatches:
    raise ParityError(f"P7-A native/Python semantic mismatch: {mismatches}")
  semantic_reference = _read(SEMANTIC_REFERENCE_PATH)
  validate_semantic_reference(semantic_reference)
  for host in (native, python_host):
    reference_mismatches = _semantic_mismatches(
      semantic_reference["semantic"],
      host["semantic"],
      f"$.hosts.{host['host_id']}.semantic",
      tolerance,
    )
    if reference_mismatches:
      raise ParityError(
        f"P7-A host drifted from the frozen semantic reference: {reference_mismatches}"
      )
  for host in (native, python_host):
    composition = host["semantic"]["composition"]
    producer_join = {
      "runtime_request_sha256": "request_sha256",
      "catalog_lock_sha256": "lock_sha256",
      "profile_projection_sha256": "profile_projection_sha256",
      "requested_manifest_sha256": "requested_manifest_sha256",
      "resolved_manifest_sha256": "resolved_manifest_sha256",
    }
    for composition_key, producer_key in producer_join.items():
      if composition[composition_key] != producer[producer_key]:
        raise ParityError(f"P7-A Cordis/host identity mismatch: {composition_key}")

  payload = {
    "schema_version": SCHEMA_VERSION,
    "evidence_version": EVIDENCE_VERSION,
    "profile": {
      "profile_id": "builtin.default_compatibility",
      "profile_version": "1.0.0",
      "backend_provider_id": "builtin.backend.flecs_cpu",
      "backend_profile_id": "cpu_exact.reference",
    },
    "workload": WORKLOAD,
    "budget": {
      "budget_id": budget["budget_id"],
      "budget_version": budget["budget_version"],
      "budget_sha256": _sha256(budget),
    },
    "semantic_reference_sha256": semantic_reference["semantic_reference_sha256"],
    "producer": producer,
    "hosts": [native, python_host],
    "semantic_comparison": {
      "status": "exact_within_budget",
      "absolute_tolerance": tolerance,
      "mismatches": [],
    },
    "budget_evaluation": evaluate_budget(native, python_host, budget),
    "node_host_status": NODE_STATUS,
    "canonicalization": CANONICALIZATION,
    "hash_algorithm": HASH_ALGORITHM,
  }
  return _seal(payload)


def validate_evidence(value: dict[str, Any]) -> None:
  _validate_schemas(BUDGET, value)
  if value.get("schema_version") != SCHEMA_VERSION:
    raise ParityError("P7-A evidence schema version mismatch")
  if value.get("node_host_status") != NODE_STATUS:
    raise ParityError("P7-A evidence widened the held Node-host boundary")
  payload = {
    key: item
    for key, item in value.items()
    if key not in {"canonical_json", "evidence_sha256"}
  }
  canonical = _canonical(payload)
  if value.get("canonical_json") != canonical:
    raise ParityError("P7-A evidence canonical JSON mismatch")
  if value.get("evidence_sha256") != hashlib.sha256(canonical.encode("utf-8")).hexdigest():
    raise ParityError("P7-A evidence SHA-256 mismatch")
  if value.get("workload") != BUDGET["workload"]:
    raise ParityError("P7-A evidence workload mismatch")
  if value.get("budget", {}).get("budget_sha256") != _sha256(BUDGET):
    raise ParityError("P7-A evidence budget identity mismatch")
  semantic_reference = _read(SEMANTIC_REFERENCE_PATH)
  validate_semantic_reference(semantic_reference)
  if value.get("semantic_reference_sha256") != semantic_reference["semantic_reference_sha256"]:
    raise ParityError("P7-A evidence semantic-reference identity mismatch")
  hosts = value.get("hosts", [])
  if [host.get("host_id") for host in hosts] != ["native_cpp_direct", "python_nanobind"]:
    raise ParityError("P7-A evidence host rows are incomplete or reordered")
  expected_host_attestation = (
    ("native_direct", "direct_executable"),
    ("python_binding", "ef_py_local_build"),
  )
  for host, (host_kind, caller_attestation) in zip(
    hosts, expected_host_attestation, strict=True
  ):
    if host.get("host_kind") != host_kind or host.get("caller_attestation") != caller_attestation:
      raise ParityError(f"P7-A host attestation mismatch: {host.get('host_id')}")
    validate_metric_consistency(host)
  for key in ("platform", "build_mode", "logical_cpu_count"):
    if hosts[0]["environment"][key] != hosts[1]["environment"][key]:
      raise ParityError(f"P7-A cross-host environment mismatch: {key}")
  tolerance = float(BUDGET["semantic"]["absolute_tolerance"])
  mismatches = _semantic_mismatches(
    hosts[0]["semantic"], hosts[1]["semantic"], "$.hosts.semantic", tolerance
  )
  if mismatches or value.get("semantic_comparison", {}).get("mismatches"):
    raise ParityError(f"P7-A evidence contains semantic mismatches: {mismatches}")
  for host in hosts:
    reference_mismatches = _semantic_mismatches(
      semantic_reference["semantic"],
      host["semantic"],
      f"$.hosts.{host['host_id']}.semantic",
      tolerance,
    )
    if reference_mismatches:
      raise ParityError(
        f"P7-A evidence drifted from the frozen semantic reference: {reference_mismatches}"
      )
    composition = host["semantic"]["composition"]
    replay = host["semantic"]["replay_comparison"]
    expected_composition_ref = f"composition_evidence_sha256={composition['evidence_sha256']}"
    evidence_refs = replay["evidence_refs"]
    if (
      replay["composition_evidence_ref"] != expected_composition_ref
      or evidence_refs.count(expected_composition_ref) != 1
      or len(evidence_refs) != 6
      or len(set(evidence_refs)) != 6
    ):
      raise ParityError(f"P7-A replay evidence refs are inconsistent: {host['host_id']}")
  if value.get("budget_evaluation", {}).get("status") != "pass":
    raise ParityError("P7-A evidence does not pass the frozen batch budget")
  if any(not check.get("passed") for check in value["budget_evaluation"]["checks"]):
    raise ParityError("P7-A evidence contains a failed budget check")
  expected_budget_evaluation = evaluate_budget(hosts[0], hosts[1], BUDGET)
  if value["budget_evaluation"] != expected_budget_evaluation:
    raise ParityError("P7-A evidence budget evaluation was not reproduced")
  producer = value["producer"]
  if producer != expected_producer_identity():
    raise ParityError("P7-A evidence producer identity does not match admitted fixtures")
  for host in hosts:
    composition = host["semantic"]["composition"]
    if composition["runtime_request_sha256"] != producer["request_sha256"]:
      raise ParityError("P7-A evidence request join mismatch")
    if composition["catalog_lock_sha256"] != producer["lock_sha256"]:
      raise ParityError("P7-A evidence lock join mismatch")
    if composition["profile_projection_sha256"] != producer["profile_projection_sha256"]:
      raise ParityError("P7-A evidence projection join mismatch")
    if composition["requested_manifest_sha256"] != producer["requested_manifest_sha256"]:
      raise ParityError("P7-A evidence requested-manifest join mismatch")
    if composition["resolved_manifest_sha256"] != producer["resolved_manifest_sha256"]:
      raise ParityError("P7-A evidence resolved-manifest join mismatch")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  subparsers = parser.add_subparsers(dest="command", required=True)
  generate = subparsers.add_parser("generate-budget")
  generate.add_argument("--out", type=Path, default=BUDGET_PATH)
  freeze = subparsers.add_parser("freeze-semantic-reference")
  freeze.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
  freeze.add_argument("--out", type=Path, default=SEMANTIC_REFERENCE_PATH)
  capture = subparsers.add_parser("capture")
  capture.add_argument("--native-binary", type=Path, required=True)
  capture.add_argument("--node", default="node")
  capture.add_argument("--out", type=Path, default=EVIDENCE_PATH)
  validate = subparsers.add_parser("validate")
  validate.add_argument("--evidence", type=Path, default=EVIDENCE_PATH)
  args = parser.parse_args(argv)

  if args.command == "generate-budget":
    write_budget(args.out)
    print(args.out)
    return 0
  if args.command == "freeze-semantic-reference":
    source = _read(args.evidence)
    hosts = source.get("hosts", [])
    if [host.get("host_id") for host in hosts] != ["native_cpp_direct", "python_nanobind"]:
      raise ParityError("semantic-reference source lacks the exact P7-A host rows")
    mismatches = _semantic_mismatches(
      hosts[0]["semantic"],
      hosts[1]["semantic"],
      "$.hosts.semantic",
      float(BUDGET["semantic"]["absolute_tolerance"]),
    )
    if mismatches:
      raise ParityError(f"semantic-reference source host mismatch: {mismatches}")
    reference = build_semantic_reference(hosts[0]["semantic"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_pretty(reference), encoding="utf-8", newline="\n")
    validate_semantic_reference(reference)
    print(args.out)
    print(reference["semantic_reference_sha256"])
    return 0
  if args.command == "capture":
    evidence = build_evidence(args.native_binary.resolve(), args.node)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_pretty(evidence), encoding="utf-8", newline="\n")
    validate_evidence(evidence)
    print(args.out)
    print(evidence["evidence_sha256"])
    return 0
  validate_evidence(_read(args.evidence))
  print(args.evidence)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
