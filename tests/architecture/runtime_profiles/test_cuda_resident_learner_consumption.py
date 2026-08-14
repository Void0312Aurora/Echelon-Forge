from __future__ import annotations

import re

from tests.architecture.helpers import REPO_ROOT


CUDA_RESIDENT_DIR = REPO_ROOT / "src/runtime/facade/internal/cuda_resident"
CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_learner_consumption_contract.h"
PROJECTION_CONTRACT = (
    REPO_ROOT / "src/runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"
)
CONSUMER_CONTRACT = REPO_ROOT / "src/runtime/contracts/cuda_resident_device_consumer_contract.h"
OBSERVATION_SOURCE = CUDA_RESIDENT_DIR / "cuda_world_store_cuda_observation.cu"
CONSUMER_SOURCE = CUDA_RESIDENT_DIR / "cuda_resident_device_consumer.cpp"
CUDA_TEST = REPO_ROOT / "src/tests/test_cuda_resident_device_consumer.cpp"


def _text(path) -> str:
    return path.read_text(encoding="utf-8")


def test_learner_consumer_reads_the_full_tensor_not_a_probe_element() -> None:
    """The maintained learner-equivalent path transforms the whole lease tensor."""
    device = _text(OBSERVATION_SOURCE)

    learner_body = device.split("__global__ void learner_equivalent_consumer_kernel", 1)[1]
    learner_body = (
        learner_body.split("__global__", 1)[0]
        if "__global__" in learner_body
        else learner_body.split("} // namespace", 1)[0]
    )
    assert "for (std::size_t field = 0; field < values_per_world; ++field)" in learner_body
    assert "values[base + field]" in learner_body
    assert "normalization.offsets[field]" in learner_body
    assert "normalization.scales[field]" in learner_body
    assert "out_ids[world] = ids[world]" in learner_body

    smoke_body = device.split("__global__ void\ndevice_observation_consumer_smoke_kernel", 1)[1]
    smoke_body = smoke_body.split("\n}", 1)[0]
    assert "values[world * values_per_world]" in smoke_body
    assert "for (" not in smoke_body

    submit = device.split("bool submit_cuda_world_store_device_observation_consumer", 1)[1]
    assert "learner_equivalent_consumer_kernel<<<" in submit
    assert "device_observation_consumer_smoke_kernel<<<" in submit
    assert submit.index("if (learner_equivalent)") < submit.index(
        "learner_equivalent_consumer_kernel<<<"
    )
    assert "kLearnerConsumptionFeatureCount" in submit
    assert "FailureCode::incompatible_layout" in submit


def test_learner_submit_and_await_have_no_hidden_host_readback() -> None:
    """Device-to-host materialization remains outside submit and await."""
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


def test_learner_policy_input_layout_and_dtype_are_pinned_to_the_contract() -> None:
    """Policy input stays world-major float32 with the packed feature count."""
    contract = _text(CONTRACT)
    projection = _text(PROJECTION_CONTRACT)
    device = _text(OBSERVATION_SOURCE)
    consumer = _text(CONSUMER_SOURCE)

    assert "kLearnerConsumptionFeatureCount = 15" in contract
    assert (
        "kLearnerConsumptionFeatureCount == kObservationProjectionObservationValueCount" in contract
    )
    assert "kObservationProjectionObservationValueCount = 15" in projection
    assert "entry.field_id != kObservationProjectionObservationFieldNames[field]" in contract
    assert "static_assert(learner_normalization_is_well_formed()" in contract

    assert "const std::size_t base = world * values_per_world;" in device
    assert "policy_inputs[base + field]" in device
    assert (
        "learner_consumption::kLearnerConsumptionFeatureCount ==\n"
        "                  kObservationProjectionObservationFieldCount" in device
    )

    assert ".shape = {raw.world_count, raw.values_per_world}" in consumer
    assert ".strides = {raw.values_per_world, 1}" in consumer
    assert '.dtype = "float32"' in consumer


def test_learner_normalization_constants_have_exactly_one_owner() -> None:
    """The live contract is the only owner of the affine normalization table."""
    contract = _text(CONTRACT)
    assert "LearnerFieldNormalization" in contract
    assert "kLearnerNormalization[kLearnerConsumptionFeatureCount]" in contract

    definition_pattern = re.compile(
        r"kLearnerNormalization\s*\[\s*kLearnerConsumptionFeatureCount\s*\]"
    )
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

    device = _text(OBSERVATION_SOURCE)
    assert "learner_consumption::kLearnerNormalization" in device


def test_native_suite_owns_the_full_tensor_cpu_parity_oracle() -> None:
    """The native suite validates the maintained path against packed CPU values."""
    contract = _text(CONTRACT)
    cuda_test = _text(CUDA_TEST)

    assert (
        'kLearnerConsumerSurfaceV1 =\n    "cuda_resident.device_consumer_learner_equivalent.v1"'
        in contract
    )
    assert "learner_equivalent = true" in cuda_test
    assert "kLearnerNormalization[field]" in cuda_test
    assert "to_packed_float" in cuda_test
