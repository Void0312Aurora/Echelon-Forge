from __future__ import annotations

from typing import Callable

from .common import ContractSkipped, _load_spec
from .env_regression import run_env_regression_contract
from .loader_command_chain import run_loader_command_chain_contract
from .route_generator import run_route_generator_contract
from .scripted_bridge import run_scripted_bridge_contract
from .unit import run_unit_regression_contract

ContractHandler = Callable[[str], tuple[bool, str]]

_CONTRACT_HANDLERS: dict[str, ContractHandler] = {
    "loader_command_chain": run_loader_command_chain_contract,
    "route_generator": run_route_generator_contract,
    "env_regression": run_env_regression_contract,
    "unit_regression": run_unit_regression_contract,
    "scripted_bridge": run_scripted_bridge_contract,
}


def run_contract(spec_path: str) -> tuple[bool, str]:
    spec = _load_spec(spec_path)
    contract_type = str(spec.get("type", "")).strip().lower()
    try:
        handler = _CONTRACT_HANDLERS[contract_type]
    except KeyError as exc:
        raise ValueError(f"Unknown contract type: {contract_type}") from exc
    return handler(spec_path)


__all__ = [
    "ContractSkipped",
    "run_contract",
    "run_env_regression_contract",
    "run_loader_command_chain_contract",
    "run_route_generator_contract",
    "run_scripted_bridge_contract",
    "run_unit_regression_contract",
]
