from __future__ import annotations

import re

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_learner_consumption_contract.h"
PROJECTION_CONTRACT = (
  REPO_ROOT / "src/runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"
)
MATRIX_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_matrix_contract.h"
CONSUMER_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_device_consumer_contract.h"
OBSERVATION_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda_observation.cu"
CONSUMER_SOURCE = CUDA_RESIDENT_DIR / "cuda_resident_device_consumer.cpp"
MATRIX_SESSION = (
  REPO_ROOT / "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.cpp"
)
MATRIX_PROBE = (
  REPO_ROOT / "src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_probe.cpp"
)
CUDA_TEST = REPO_ROOT / "src/tests/test_cuda_resident_device_consumer.cpp"


def _text(path) -> str:
  return path.read_text(encoding="utf-8")


def test_cp6_learner_consumer_reads_the_full_tensor_not_a_probe_element() -> None:
  """Gate G-C's measured consumer must be learner-equivalent: every element of
  the lease tensor is read and transformed. The smoke kernel stays available
  for lifecycle coverage but can never satisfy this gate, and the learner
  submission path is the one that launches the full-tensor kernel."""
  device = _text(OBSERVATION_SOURCE)

  learner_body = device.split("__global__ void learner_equivalent_consumer_kernel", 1)[1]
  learner_body = learner_body.split("__global__", 1)[0] if "__global__" in learner_body else (
    learner_body.split("} // namespace", 1)[0]
  )
  # Full-tensor read: a per-field loop over values_per_world indexes the lease
  # payload at [world * values_per_world + field].
  assert "for (std::size_t field = 0; field < values_per_world; ++field)" in learner_body
  assert "values[base + field]" in learner_body
  # Normalization applies the contract-owned affine transform per field.
  assert "normalization.offsets[field]" in learner_body
  assert "normalization.scales[field]" in learner_body
  # Ids pass through unchanged with epoch semantics owned by the lease layer.
  assert "out_ids[world] = ids[world]" in learner_body

  # The smoke kernel remains a single-element boundary probe.
  smoke_body = device.split("__global__ void\ndevice_observation_consumer_smoke_kernel", 1)[1]
  smoke_body = smoke_body.split("\n}", 1)[0]
  assert "values[world * values_per_world]" in smoke_body
  assert "for (" not in smoke_body

  # The submit path selects the learner kernel for learner_equivalent requests
  # and enforces the fifteen-field layout before launching.
  submit = device.split("bool submit_cuda_world_store_device_observation_consumer", 1)[1]
  assert "learner_equivalent_consumer_kernel<<<" in submit
  assert "device_observation_consumer_smoke_kernel<<<" in submit
  assert submit.index("if (learner_equivalent)") < submit.index(
    "learner_equivalent_consumer_kernel<<<"
  )
  assert "kLearnerConsumptionFeatureCount" in submit
  assert "FailureCode::incompatible_layout" in submit


def test_cp6_measured_path_has_no_hidden_host_readback() -> None:
  """CR2-3's measurement discipline carries over: submit and await contain no
  device-to-host copies; the only D2H stays in the explicitly diagnostic
  materialization outside the timed path."""
  device = _text(OBSERVATION_SOURCE)
  submit = device.split("bool submit_cuda_world_store_device_observation_consumer", 1)[1].split(
    "bool await_cuda_world_store_device_observation_consumer", 1
  )[0]
  await_section = device.split("bool await_cuda_world_store_device_observation_consumer", 1)[
    1
  ].split("bool materialize_cuda_world_store_device_observation_consumer", 1)[0]
  assert "cudaMemcpy" not in submit
  assert "cudaMemcpy" not in await_section

  contract = _text(CONSUMER_CONTRACT)
  assert "kDeviceConsumerMeasuredPathIncludesHostValidationReadback = false" in contract
  assert "kDeviceConsumerDiagnosticReadbackIsOutsideMeasuredPath = true" in contract


def test_cp6_policy_input_layout_and_dtype_are_pinned_to_the_contract() -> None:
  """The policy input buffer shares the lease payload's layout family:
  world-major [world_count, feature_count] float32 with element strides, and
  the feature count is statically tied to the packed observation layout."""
  contract = _text(CONTRACT)
  projection = _text(PROJECTION_CONTRACT)
  device = _text(OBSERVATION_SOURCE)
  consumer = _text(CONSUMER_SOURCE)

  assert "kLearnerConsumptionFeatureCount = 15" in contract
  assert (
    "kLearnerConsumptionFeatureCount == kObservationProjectionObservationValueCount" in contract
  )
  assert "kObservationProjectionObservationValueCount = 15" in projection
  # Field identities must follow the projection contract's packed order; the
  # contract enforces this in a consteval well-formedness gate.
  assert "entry.field_id != kObservationProjectionObservationFieldNames[field]" in contract
  assert "static_assert(learner_normalization_is_well_formed()" in contract

  # The kernel writes world-major rows.
  assert "const std::size_t base = world * values_per_world;" in device
  assert "policy_inputs[base + field]" in device
  # The device layer asserts the packed layout equality once more at compile
  # time next to the kernels.
  assert (
    "learner_consumption::kLearnerConsumptionFeatureCount ==\n"
    "                  kObservationProjectionObservationFieldCount" in device
  )

  # The receipt advertises the output tensor with the same descriptor family
  # the lease uses: [world_count, values_per_world] float32, element strides.
  assert ".shape = {raw.world_count, raw.values_per_world}" in consumer
  assert ".strides = {raw.values_per_world, 1}" in consumer
  assert '.dtype = "float32"' in consumer


def test_cp6_normalization_constants_have_exactly_one_owner() -> None:
  """The affine constants live in the contract header alone. The kernel
  receives them by value from the contract table, so no second table may
  exist anywhere in sources, tools, or scripts."""
  contract = _text(CONTRACT)
  assert "LearnerFieldNormalization" in contract
  assert "kLearnerNormalization[kLearnerConsumptionFeatureCount]" in contract

  # Match the array *definition* (declared against the feature-count constant),
  # not subscripted reads like kLearnerNormalization[field].
  definition_pattern = re.compile(r"kLearnerNormalization\s*\[\s*kLearnerConsumptionFeatureCount\s*\]")
  owners = []
  for root in ("src", "tools", "scripts"):
    base = REPO_ROOT / root
    if not base.exists():
      continue
    for path in base.rglob("*"):
      if path.suffix not in {".h", ".hpp", ".cuh", ".cu", ".cpp", ".py"}:
        continue
      text = path.read_text(encoding="utf-8", errors="ignore")
      if definition_pattern.search(text):
        owners.append(path)
  assert owners == [CONTRACT]

  # Consumers reference the table through the contract namespace only.
  device = _text(OBSERVATION_SOURCE)
  assert "learner_consumption::kLearnerNormalization" in device


def test_cp6_mode_id_is_owned_by_the_contract_and_stays_out_of_the_frozen_table() -> None:
  """CP-6 measures through an explicit probe flag. The mode id has exactly one
  owner (the learner contract); the frozen CR2-6a mode table keeps its four
  modes because the matrix evidence validators are still single-generation
  pinned -- extending that table is the CP-8 re-matrix lane."""
  contract = _text(CONTRACT)
  matrix_contract = _text(MATRIX_CONTRACT)
  probe = _text(MATRIX_PROBE)
  session = _text(MATRIX_SESSION)

  assert 'kLearnerConsumerModeIdNoExport =\n    "no_export_learner_consumer"' in contract
  assert "no_export_learner_consumer" not in matrix_contract
  assert matrix_contract.count("mode_ids_are_unique") >= 1

  # The probe appends the learner mode only behind the explicit flag and takes
  # the id from the contract constant instead of a second literal.
  assert '"--learner-consumer"' in probe
  assert "args.learner_consumer_mode" in probe
  assert "kLearnerConsumerModeIdNoExport" in probe
  assert '"no_export_learner_consumer"' not in probe

  # The session forwards the mode kind into the consumer request, so the
  # learner mode measures the learner kernel and the frozen modes keep the
  # smoke consumer for CR2-6b comparability.
  assert ".learner_equivalent = mode.learner_consumer" in session

  # The C++ suite closes the loop with a CPU-reference parity oracle over the
  # full normalized tensor.
  cuda_test = _text(CUDA_TEST)
  assert "learner_equivalent = true" in cuda_test
  assert "kLearnerNormalization[field]" in cuda_test
  assert "to_packed_float" in cuda_test
