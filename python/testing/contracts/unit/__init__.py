from __future__ import annotations

from typing import Callable

from python.testing.runtime import ensure_repo_imports

from ..common import _load_spec
from .comm import run_comm_contract
from .kernel import run_kernel_contract
from .leader import run_leader_contract
from .misc import run_misc_contract
from .wrapper import run_wrapper_contract

UnitHandler = Callable[[str, dict[str, object]], tuple[bool, str] | None]


def run_unit_regression_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    spec = _load_spec(spec_path)
    check_kind = str(spec.get("check_kind", "")).strip().lower()
    handlers: tuple[UnitHandler, ...] = (
        run_wrapper_contract,
        run_kernel_contract,
        run_comm_contract,
        run_leader_contract,
        run_misc_contract,
    )
    for handler in handlers:
        result = handler(check_kind, spec)
        if result is not None:
            return result
    raise ValueError(f"Unknown unit_regression check_kind: {check_kind}")
