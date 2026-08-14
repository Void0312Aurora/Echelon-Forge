from __future__ import annotations

from python.runtime_bootstrap import ensure_repo_imports

from ..common import _load_spec
from .comm import _COMM_CONTRACT_CHECKS, run_comm_contract
from .kernel import _KERNEL_CONTRACT_CHECKS, run_kernel_contract
from .leader import _LEADER_CONTRACT_CHECKS, run_leader_contract
from .misc import _MISC_CONTRACT_CHECKS, run_misc_contract
from .wrapper import _WRAPPER_CONTRACT_CHECKS, run_wrapper_contract

__all__ = [
    "run_comm_contract",
    "run_kernel_contract",
    "run_leader_contract",
    "run_misc_contract",
    "run_wrapper_contract",
    "run_unit_regression_contract",
]


def _merged_contract_checks():
    merged = {}
    for table in (
        _WRAPPER_CONTRACT_CHECKS,
        _KERNEL_CONTRACT_CHECKS,
        _COMM_CONTRACT_CHECKS,
        _LEADER_CONTRACT_CHECKS,
        _MISC_CONTRACT_CHECKS,
    ):
        duplicates = merged.keys() & table.keys()
        if duplicates:
            raise RuntimeError(f"duplicate unit contract check_kind registrations: {sorted(duplicates)}")
        merged.update(table)
    return merged


_UNIT_CONTRACT_CHECKS = _merged_contract_checks()


def run_unit_regression_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    spec = _load_spec(spec_path)
    check_kind = str(spec.get("check_kind", "")).strip().lower()
    handler = _UNIT_CONTRACT_CHECKS.get(check_kind)
    if handler is None:
        raise ValueError(f"Unknown unit_regression check_kind: {check_kind}")
    return handler(spec)
