from __future__ import annotations

import re

from tests.architecture.runtime_facade.helpers import *
from tests.support.xmacro_text import expand_header_field_incs


def test_runtime_contract_headers_do_not_include_engine_headers() -> None:
  header_paths = [
    *RUNTIME_CONTRACTS.glob("*.h"),
    *RUNTIME_FACADE.glob("*_types.h"),
  ]
  violations: list[tuple[str, int, str]] = []
  for path in header_paths:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
      stripped = line.strip()
      if stripped.startswith("#include") and '"core/engine/' in stripped:
        violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

  assert not violations, f"runtime contract/facade type headers include engine headers: {violations}"

def test_runtime_facade_public_header_hides_engine_owner_storage() -> None:
  header = (RUNTIME_FACADE / "runtime_facade.h").read_text(encoding="utf-8")
  assert '#include "core/engine/world_batch_runtime.h"' not in header
  assert "class WorldBatchRuntime;" in header
  assert "std::unique_ptr<WorldBatchRuntime>" in header

def test_runtime_facade_does_not_include_or_call_gpu_helpers() -> None:
  gpu_markers = (
    '#include "gpu/',
    "#include <gpu/",
    "gpu::",
    "probe_gpu_device",
    "probe_device(",
    "last_visual_experiment_stats",
    "last_execution_observation_stats",
    "last_flight_shaping_stats",
    "device_resident",
    "last_visual_output_device_ptr",
    "last_execution_observation_output_device_ptr",
    "last_flight_shaping_output_device_ptr",
  )
  violations: list[tuple[str, str]] = []
  for path in sorted(RUNTIME_FACADE.glob("*")):
    if path.suffix not in {".h", ".cpp"}:
      continue
    source = path.read_text(encoding="utf-8")
    for marker in gpu_markers:
      if marker in source:
        violations.append((str(path.relative_to(REPO_ROOT)), marker))

  assert not violations, f"RuntimeFacade must not depend on GPU helper/probe implementation: {violations}"

def test_runtime_facade_capabilities_stay_independent_from_cuda_experiment_signals() -> None:
  source = runtime_facade_source_text()
  capabilities_body = source.split("RuntimeCapabilities RuntimeFacade::capabilities() const noexcept {", 1)[1]
  capabilities_body = capabilities_body.split(
    "RuntimeFidelityAdmission RuntimeFacade::admit_fidelity_request(",
    1,
  )[0]

  forbidden_markers = (
    "EF_ENABLE_CUDA_EXPERIMENTS",
    "cuda_runtime_built",
    "cuda_runtime_available",
    "device_count",
    "active_device",
    "compute_major",
    "compute_minor",
    "runtime_version",
    "free_global_mem_bytes",
    "total_global_mem_bytes",
    "device_name",
    "error_message",
    "probe_gpu_device",
    "gpu::probe_device",
    "last_visual_experiment_stats",
    "last_execution_observation_stats",
    "last_flight_shaping_stats",
    "used_cuda",
    "device_view",
    "device_ptr",
    "last_visual_output_device_ptr",
    "last_execution_observation_output_device_ptr",
    "last_flight_shaping_output_device_ptr",
  )
  violations = [marker for marker in forbidden_markers if marker in capabilities_body]
  assert not violations, (
    "RuntimeFacade.capabilities() must stay fail-closed and must not read CUDA "
    f"availability/helper/probe/device-resident signals: {violations}"
  )

def test_runtime_binding_capability_surface_keeps_gpu_helper_signals_separate() -> None:
  source = RUNTIME_BINDINGS.read_text(encoding="utf-8")
  runtime_capabilities_block = source.split('nb::class_<RuntimeCapabilities>', 1)[1]
  runtime_capabilities_block = runtime_capabilities_block.split(
    'nb::class_<RuntimeBatchConfig>',
    1,
  )[0]
  assert "cuda_runtime_available" not in runtime_capabilities_block
  assert "probe_gpu_device" not in runtime_capabilities_block
  assert "used_cuda" not in runtime_capabilities_block

def test_backend_profile_contract_marks_gpu_helpers_export_only_and_non_promoting() -> None:
  header = (RUNTIME_CONTRACTS / "backend_profile_contracts.h").read_text(encoding="utf-8")
  diagnostics_only_match = re.search(
    r"BackendProfileContract\{\s*"
    r"\.backend_profile_id\s*=\s*std::string\(kBackendProfileIdGpuHelpersDiagnosticsOnly\),"
    r"(?P<body>.*?)"
    r"BackendProfileContract\{\s*"
    r"\.backend_profile_id\s*=\s*std::string\(kBackendProfileIdGpuExactUnmaintainedCandidate\),",
    header,
    flags=re.DOTALL,
  )
  assert diagnostics_only_match is not None
  diagnostics_only_profile = diagnostics_only_match.group("body")

  required_markers = (
    '.sync_policy = std::string(kBackendProfileSyncPolicyExportOnly)',
    "helper-local diagnostics buffers or probes only",
    "do not affect committed state",
    "never maintained state",
    "support stay false",
    "cannot accept it as maintained parity",
    ".exact_gpu_supported = false",
    ".resident_state_supported = false",
    ".shadow_supported = false",
    ".device_observation_view_supported = false",
  )
  missing = [marker for marker in required_markers if marker not in diagnostics_only_profile]
  assert not missing, (
    "GPU helper diagnostics-only backend profile drifted away from the WP19-C non-promotion "
    f"boundary: {missing}"
  )

def test_core_runtime_does_not_probe_gpu_for_facade_capability_projection() -> None:
  forbidden_markers = (
    "RuntimeCapabilities",
    "supports_exact_gpu_backend",
    "supports_resident_state",
    "supports_shadow_compare",
    "probe_gpu_device",
    "gpu::probe_device",
    "last_visual_experiment_stats",
    "last_execution_observation_stats",
    "last_flight_shaping_stats",
    "last_visual_output_device_ptr",
    "last_execution_observation_output_device_ptr",
    "last_flight_shaping_output_device_ptr",
  )
  violations: list[tuple[str, str]] = []
  for path in sorted(CORE_SRC.rglob("*")):
    if path.suffix not in {".h", ".cpp", ".cc", ".cxx"}:
      continue
    source = path.read_text(encoding="utf-8")
    for marker in forbidden_markers:
      if marker in source:
        violations.append((str(path.relative_to(REPO_ROOT)), marker))

  assert not violations, f"core runtime must not project maintained GPU/resident/shadow capabilities: {violations}"

def test_resident_state_candidate_stays_fail_closed_and_exports_remain_host_visible() -> None:
  contracts = (RUNTIME_CONTRACTS / "backend_profile_contracts.h").read_text(encoding="utf-8")
  # ObservationBatchPacket's provenance field is schema-owned (I31): expand
  # the X-macro #include so this still matches the compiled field shape.
  facade_types = expand_header_field_incs(
    (RUNTIME_FACADE / "runtime_facade_types.h").read_text(encoding="utf-8")
  )
  facade_cpp = runtime_facade_source_text()

  assert "kBackendProfileIdResidentStateUnmaintainedCandidate" in contracts
  resident_section = contracts.split("kBackendProfileIdResidentStateUnmaintainedCandidate", 1)[1]
  assert ".sync_policy = std::string(kBackendProfileSyncPolicyUndeclaredBlocked)" in resident_section
  assert ".maintained_status =" in resident_section
  assert "kBackendProfileMaintainedStatusUnmaintainedCandidate" in resident_section
  assert ".resident_state_supported = false" in resident_section
  assert "Candidate backend-resident operational shards are not maintained truth." in resident_section
  assert "Blocked until ownership split, sync cadence/trigger, barriers, host-visible reconstruction/export" in resident_section

  capabilities_section = facade_cpp.split("RuntimeCapabilities RuntimeFacade::capabilities() const noexcept", 1)[1]
  assert ".supports_resident_state = false" in capabilities_section
  assert ".resident_state_candidate_profile_id =" in capabilities_section
  assert ".resident_state_candidate_parity_budget_ref =" in capabilities_section
  assert ".resident_state_rejection_reason =" in capabilities_section

  observation_packet_section = facade_types.split("struct ObservationBatchPacket", 1)[1].split("struct EngagementEventPacket", 1)[0]
  assert 'std::string barrier_id = "export";' in observation_packet_section
  assert "kPolicySourceLabelFacadeObservationPacket" in observation_packet_section
  assert "kPolicyMaintainedStatusMaintained" in observation_packet_section

  engagement_packet_section = facade_types.split("struct EngagementEventPacket", 1)[1].split("struct ExecutionBatchStepResult", 1)[0]
  assert 'std::string barrier_id = "export";' in engagement_packet_section
  assert 'std::string barrier_detail = "maintained_facade_export";' in engagement_packet_section
  assert "kPolicySourceLabelTrackStatePacket" in engagement_packet_section
  assert "kPolicySourceLabelWorldTruthDiagnostics" in engagement_packet_section
  assert "kPolicyMaintainedStatusDiagnosticsOnly" in engagement_packet_section
