from pathlib import Path

import pytest

from tools.diagnostics.cuda_resident_cr2_full_window_compare import compare


ROOT = Path(__file__).resolve().parents[3]
PROBE = ROOT / "src/tools/experimental/cuda_resident/cuda_resident_full_window_probe.cpp"
COMPARATOR = ROOT / "tools/diagnostics/cuda_resident_cr2_full_window_compare.py"
CONTRACT = ROOT / "src/runtime/contracts/cuda_resident_full_window_contract.h"
RUNNER = ROOT / "src/runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.cpp"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_full_window_probe_has_two_real_lane_build_definitions() -> None:
    cmake = _text(ROOT / "CMakeLists.txt")
    probe = _text(PROBE)

    assert "ef_cuda_resident_full_window_cpu_probe" in cmake
    assert "ef_cuda_resident_full_window_cuda_probe" in cmake
    assert "EF_CR2_FULL_WINDOW_CPU_PROBE=1" in cmake
    assert "EF_CR2_FULL_WINDOW_CUDA_PROBE=1" in cmake
    assert "make_unique<FlecsCpuBackend>" in probe
    assert "make_unique<runtime::cuda_resident::CudaResidentBackend>" in probe


def test_full_window_runner_owns_common_sequence_and_poison_contract() -> None:
    contract = _text(CONTRACT)
    runner = _text(RUNNER)

    for operation in ("setup", "input_injection", "evaluation", "advance", "export_state"):
        assert operation in contract
    for barrier in ("input_injection", "window_commit", "export"):
        assert barrier in contract
    assert "backend_->setup" in runner
    assert "backend_->inject" in runner
    assert "backend_->evaluate({})" in runner
    assert "backend_->advance" in runner
    assert "backend_->export_state" in runner
    assert "export_identity_mismatch" in contract
    assert "source_barrier" in contract
    assert "capture_barrier" in contract
    assert "poisoned_ = true" in runner
    assert "publish_stage" not in runner


def test_full_window_comparator_compares_only_common_surface_projection() -> None:
    comparator = _text(COMPARATOR)

    assert "json.loads(completed.stdout)" in comparator
    assert "common surface or operation projection diverged" in comparator
    assert '"trace_signature"' in comparator
    assert '"operations"' in comparator
    assert '"backend_id"' in comparator


def _payload(lane: str, backend_id: str) -> dict[str, object]:
    return {
        "schema_version": "cuda_resident.full_window_probe.v1",
        "surface_id": "cuda_resident.full_window_spi.v1",
        "trace_signature": "trace",
        "operations": [{"operation": "setup", "succeeded": True}],
        "completed": True,
        "failure": None,
        "lane": lane,
        "backend_id": backend_id,
    }


def test_full_window_comparator_accepts_lane_local_identifiers() -> None:
    summary = compare(
        _payload("cpu_reference", "flecs_cpu_reference"),
        _payload("cuda_resident", "cuda_resident.rb7_phase_d"),
    )

    assert summary["common_sequence_equal"] is True
    assert summary["operation_count"] == 1


def test_full_window_comparator_rejects_operation_divergence() -> None:
    cpu = _payload("cpu_reference", "flecs_cpu_reference")
    cuda = _payload("cuda_resident", "cuda_resident.rb7_phase_d")
    cuda["operations"] = []

    with pytest.raises(RuntimeError, match="projection diverged"):
        compare(cpu, cuda)
