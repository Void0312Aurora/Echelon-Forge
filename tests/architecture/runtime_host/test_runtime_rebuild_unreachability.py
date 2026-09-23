from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.maintenance import runtime_rebuild_unreachability as rebuild_inventory


ROOT = Path(__file__).resolve().parents[3]


def test_rebuild_inventory_is_fresh_and_pre_cutover_only() -> None:
    record = rebuild_inventory.load_fixture()
    rebuild_inventory.validate_inventory(record)

    assert record["production_callable_references"] == {}
    assert record["python_binding_references"] == {}
    assert record["test_only_references"] == {
        "src/tests/test_simulation_kernel_smoke.cpp": [79, 86, 97, 103, 140, 191, 201, 243]
    }
    assert record["reachability_state"] == "quarantined_before_production_cutover"
    assert record["retired"] is False
    assert all(record["production_package_guard"].values())


def test_rebuild_inventory_rejects_a_forged_production_caller() -> None:
    record = rebuild_inventory.load_fixture()
    forged = copy.deepcopy(record)
    forged["production_callable_references"] = {"src/main.cpp": [1]}
    with pytest.raises(rebuild_inventory.InventoryError, match="stale"):
        rebuild_inventory.validate_inventory(forged)


def test_rebuild_inventory_does_not_authorize_retirement() -> None:
    record = rebuild_inventory.load_fixture()
    forged = copy.deepcopy(record)
    forged["retired"] = True
    with pytest.raises(rebuild_inventory.InventoryError, match="stale|retirement"):
        rebuild_inventory.validate_inventory(forged)
