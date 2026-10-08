from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.maintenance import runtime_rebuild_unreachability as rebuild_inventory


ROOT = Path(__file__).resolve().parents[3]


def test_rebuild_inventory_is_fresh_and_production_authority_is_retired() -> None:
    record = rebuild_inventory.load_fixture()
    rebuild_inventory.validate_inventory(record)

    assert record["production_callable_references"] == {}
    assert record["python_binding_references"] == {}
    assert record["test_only_references"] == {
        "src/core/engine/testing/simulation_kernel_composition_test_access.cpp": [14, 16],
        "src/core/engine/testing/simulation_kernel_composition_test_access.h": [17],
        "src/tests/test_simulation_kernel_smoke.cpp": [80, 88, 100, 107, 145, 197, 209, 252],
    }
    assert record["reachability_state"] == "retired_production_authority_test_seam_retained"
    assert record["retired"] is True
    assert all(record["production_package_guard"].values())


def test_rebuild_inventory_rejects_a_forged_production_caller() -> None:
    record = rebuild_inventory.load_fixture()
    forged = copy.deepcopy(record)
    forged["production_callable_references"] = {"src/main.cpp": [1]}
    with pytest.raises(rebuild_inventory.InventoryError, match="stale"):
        rebuild_inventory.validate_inventory(forged)


def test_rebuild_inventory_rejects_unretired_state() -> None:
    record = rebuild_inventory.load_fixture()
    forged = copy.deepcopy(record)
    forged["retired"] = False
    with pytest.raises(rebuild_inventory.InventoryError, match="stale|retirement"):
        rebuild_inventory.validate_inventory(forged)
