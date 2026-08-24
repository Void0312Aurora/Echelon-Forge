from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
import pytest

from tools.maintenance import runtime_host_batch_parity_contract as parity


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
BUDGET_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_host_batch_parity_budget.v1.schema.json"
)
EVIDENCE_SCHEMA_PATH = REPO_ROOT / (
  "src/runtime/contracts/composition/runtime_host_batch_parity.v1.schema.json"
)


def _read(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def _validators() -> tuple[Draft202012Validator, Draft202012Validator]:
  budget_schema = _read(BUDGET_SCHEMA_PATH)
  evidence_schema = _read(EVIDENCE_SCHEMA_PATH)
  Draft202012Validator.check_schema(budget_schema)
  Draft202012Validator.check_schema(evidence_schema)
  registry = Registry().with_resource(
    budget_schema["$id"], Resource.from_contents(budget_schema)
  )
  return (
    Draft202012Validator(budget_schema),
    Draft202012Validator(evidence_schema, registry=registry),
  )


def _native_probe_binary() -> Path | None:
  suffix = ".exe" if os.name == "nt" else ""
  candidates: list[Path] = []
  configured = os.environ.get("CMO_BUILD_DIR", "").strip()
  if configured:
    build = Path(configured)
    if not build.is_absolute():
      build = REPO_ROOT / build
    candidates.append(build / f"ef_composition_evidence_test{suffix}")
  candidates.extend(
    REPO_ROOT / name / f"ef_composition_evidence_test{suffix}"
    for name in ("build", "build-workshop", "build-local-win", "build-p3b2")
  )
  return next((candidate for candidate in candidates if candidate.is_file()), None)


def test_p7_budget_and_reference_evidence_are_schema_valid_and_fresh() -> None:
  budget_validator, evidence_validator = _validators()
  budget = _read(parity.BUDGET_PATH)
  evidence = _read(parity.EVIDENCE_PATH)
  semantic_reference = _read(parity.SEMANTIC_REFERENCE_PATH)

  budget_validator.validate(budget)
  evidence_validator.validate(evidence)
  assert budget == parity.BUDGET
  parity.validate_semantic_reference(semantic_reference)
  parity.validate_evidence(evidence)
  assert evidence["semantic_reference_sha256"] == semantic_reference[
    "semantic_reference_sha256"
  ]
  assert evidence["node_host_status"] == "conditional_held_p6b_not_admitted"
  assert [row["host_id"] for row in evidence["hosts"]] == [
    "native_cpp_direct",
    "python_nanobind",
  ]
  assert {row["execution_owner"] for row in evidence["hosts"]} == {"native_cpp"}
  assert evidence["producer"]["producer_id"] == "cordis"
  assert evidence["semantic_comparison"] == {
    "status": "exact_within_budget",
    "absolute_tolerance": 1e-12,
    "mismatches": [],
  }
  assert evidence["budget_evaluation"]["status"] == "pass"
  assert len(evidence["budget_evaluation"]["checks"]) == 27


def test_p7_evidence_fails_closed_for_identity_node_and_budget_tampering() -> None:
  evidence = _read(parity.EVIDENCE_PATH)
  candidates = []

  request_mismatch = deepcopy(evidence)
  request_mismatch["producer"]["request_sha256"] = "0" * 64
  candidates.append(request_mismatch)

  node_widening = deepcopy(evidence)
  node_widening["node_host_status"] = "admitted"
  candidates.append(node_widening)

  failed_budget = deepcopy(evidence)
  failed_budget["budget_evaluation"]["checks"][0]["passed"] = False
  candidates.append(failed_budget)

  semantic_drift = deepcopy(evidence)
  semantic_drift["hosts"][1]["semantic"]["final_observations"][0]["x"] += 1e-6
  candidates.append(semantic_drift)

  extra_field = deepcopy(evidence)
  extra_field["unadmitted_claim"] = True
  candidates.append(extra_field)

  provenance_forgery = deepcopy(evidence)
  provenance_forgery["producer"]["package_provenance_sha256"] = "1" * 64
  candidates.append(provenance_forgery)

  metric_forgery = deepcopy(evidence)
  forged_metrics = metric_forgery["hosts"][0]["metrics"]
  forged_metrics["step_ms_per_batch"] = 1e12
  forged_metrics["reset_ms_per_batch"] = 1e12
  forged_metrics["sampled_peak_rss_bytes"] = 10**15
  forged_metrics["rss_after_teardown_bytes"] = 10**15
  candidates.append(metric_forgery)

  swapped_attestation = deepcopy(evidence)
  swapped_attestation["hosts"][0]["host_kind"] = "python_binding"
  swapped_attestation["hosts"][0]["caller_attestation"] = "ef_py_local_build"
  swapped_attestation["hosts"][1]["host_kind"] = "native_direct"
  swapped_attestation["hosts"][1]["caller_attestation"] = "direct_executable"
  candidates.append(swapped_attestation)

  large_integer_alias = deepcopy(evidence)
  large_integer_alias["hosts"][0]["semantic"]["initial_observations"][0]["entity_id"] = 2**53
  large_integer_alias["hosts"][1]["semantic"]["initial_observations"][0]["entity_id"] = 2**53 + 1
  candidates.append(large_integer_alias)

  shared_semantic_regression = deepcopy(evidence)
  for host in shared_semantic_regression["hosts"]:
    host["semantic"]["final_observations"][0]["x"] += 1_000_000.0
  candidates.append(shared_semantic_regression)

  forged_composition_comparison = deepcopy(evidence)
  for host in forged_composition_comparison["hosts"]:
    composition = host["semantic"]["composition"]
    composition["executable_graph_sha256"] = "0" * 64
    composition["evidence_sha256"] = "1" * 64
    composition_ref = f"composition_evidence_sha256={composition['evidence_sha256']}"
    comparison = host["semantic"]["composition_comparison"]
    comparison["evidence_ref"] = composition_ref
  candidates.append(forged_composition_comparison)

  decreasing_high_water = deepcopy(evidence)
  for host in decreasing_high_water["hosts"]:
    metrics = host["metrics"]
    metrics["peak_rss_before_bytes"] = 2
    metrics["peak_rss_after_bytes"] = 1
    metrics["peak_rss_delta_bytes"] = 0
    metrics["peak_rss_delta_bytes_per_world"] = 0.0
  decreasing_high_water["budget_evaluation"] = parity.evaluate_budget(
    decreasing_high_water["hosts"][0], decreasing_high_water["hosts"][1], parity.BUDGET
  )
  candidates.append(decreasing_high_water)

  zero_time_metrics = deepcopy(evidence)
  duration_names = (
    "cold_construct_ms",
    "warm_construct_ms",
    "setup_ms",
    "step_ms_per_batch",
    "step_ms_per_world",
    "reset_ms_per_batch",
    "reset_ms_per_world",
    "teardown_ms",
  )
  for host in zero_time_metrics["hosts"]:
    for name in duration_names:
      host["metrics"][name] = 0.0
  zero_time_metrics["budget_evaluation"] = parity.evaluate_budget(
    zero_time_metrics["hosts"][0], zero_time_metrics["hosts"][1], parity.BUDGET
  )
  candidates.append(zero_time_metrics)

  zero_rss_metrics = deepcopy(evidence)
  current_rss_names = (
    "rss_before_bytes",
    "rss_after_construct_bytes",
    "rss_after_setup_bytes",
    "rss_after_steps_bytes",
    "rss_after_resets_bytes",
    "rss_after_teardown_bytes",
    "sampled_peak_rss_bytes",
    "sampled_peak_delta_bytes",
    "teardown_residual_bytes",
  )
  for host in zero_rss_metrics["hosts"]:
    for name in current_rss_names:
      host["metrics"][name] = 0
    host["metrics"]["sampled_peak_delta_bytes_per_world"] = 0.0
    host["metrics"]["teardown_residual_bytes_per_world"] = 0.0
    host["metrics"]["peak_rss_before_bytes"] = 1
    host["metrics"]["peak_rss_after_bytes"] = 1
    host["metrics"]["peak_rss_delta_bytes"] = 0
    host["metrics"]["peak_rss_delta_bytes_per_world"] = 0.0
  zero_rss_metrics["budget_evaluation"] = parity.evaluate_budget(
    zero_rss_metrics["hosts"][0], zero_rss_metrics["hosts"][1], parity.BUDGET
  )
  candidates.append(zero_rss_metrics)

  cross_host_environment_mismatch = deepcopy(evidence)
  python_environment = cross_host_environment_mismatch["hosts"][1]["environment"]
  python_environment["platform"] = "linux"
  python_environment["build_mode"] = "debug"
  python_environment["logical_cpu_count"] = 999
  candidates.append(cross_host_environment_mismatch)

  for candidate in candidates:
    resealed = parity._seal(candidate)
    with pytest.raises(parity.ParityError):
      parity.validate_evidence(resealed)


def test_p7_native_probe_is_wired_to_the_maintained_facade_and_fixed_workload() -> None:
  source = (REPO_ROOT / "src/tests/test_composition_evidence.cpp").read_text(
    encoding="utf-8"
  )
  assert 'TEST_CASE("P7-A default CPU-exact native host and batch parity probe")' in source
  assert "RuntimeFacade facade(config);" in source
  assert "RuntimeFacade>(config)" in source
  assert "kParityMeasurementWorldCount = 32" in source
  assert "kParitySemanticSteps = 3" in source
  assert '"conditional_held_p6b_not_admitted"' in source
  assert "facade.step_batch()" in source
  assert "facade.set_pilot_actions_batch(actions)" in source
  assert "parity_window_trace(window)" in source
  assert "facade.compare_composition_evidence(composition.evidence)" in source
  assert "facade->reset_batch()" in source


def test_p7_live_native_python_and_cordis_producer_parity(tmp_path: Path) -> None:
  binary = _native_probe_binary()
  node = shutil.which("node")
  cordis_dependency = REPO_ROOT / "packages/cordis-runtime/node_modules/cordis/package.json"
  if binary is None or node is None or not cordis_dependency.is_file():
    if os.environ.get("CI", "").lower() == "true":
      pytest.fail("CI lacks the P7-A native probe, Node, or installed Cordis dependency")
    pytest.skip("local P7-A native probe, Node, or Cordis dependency is unavailable")

  output = tmp_path / "runtime_host_batch_parity.v1.json"
  result = subprocess.run(
    [
      os.fspath(Path(sys.executable)),
      os.fspath(REPO_ROOT / "tools/maintenance/runtime_host_batch_parity_contract.py"),
      "capture",
      "--native-binary",
      os.fspath(binary),
      "--node",
      node,
      "--out",
      os.fspath(output),
    ],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  live = _read(output)
  _, evidence_validator = _validators()
  evidence_validator.validate(live)
  parity.validate_evidence(live)
  assert live["semantic_comparison"]["mismatches"] == []
  assert all(check["passed"] for check in live["budget_evaluation"]["checks"])
