from __future__ import annotations

from pathlib import Path

import pytest

# Governance-audit tier assignment for the retained CUDA-resident evidence
# modules whose exact line counts are pinned by the frozen CR2 size policy
# (tests/fixtures/runtime_profiles/cuda_resident_program_2/
# cuda_resident_runtime_program_2_size_policy_20260731.json, enforced by
# test_cuda_resident_program_2_size_policy.py). Editing those files to add a
# module-level ``pytestmark`` would invalidate the sealed inventory, so the
# marker is applied here instead. Audit-tier modules in this directory that
# are not line-count pinned carry the module-level ``pytestmark`` directly.
# The counter/resource evidence modules are also line-count pinned but stay in
# the guard tier: their substance is C++ contract/CMake topology and
# parser/schema rejection paths, with only a minority of retained-evidence
# checks.
GOVERNANCE_AUDIT_TIER_MODULES = frozenset(
  {
    "test_cuda_resident_closure.py",
    "test_cuda_resident_cr2_closure.py",
    "test_cuda_resident_cr2_matrix_evidence.py",
  }
)

_THIS_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
  for item in items:
    path = Path(str(item.path)).resolve()
    if path.parent == _THIS_DIR and path.name in GOVERNANCE_AUDIT_TIER_MODULES:
      item.add_marker(pytest.mark.governance_audit)
