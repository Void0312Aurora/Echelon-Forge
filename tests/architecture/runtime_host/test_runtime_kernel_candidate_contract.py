from __future__ import annotations

import copy
from pathlib import Path

import pytest

from python.rl.runtime.world_batch.candidate_adapter import EpochEntityRef
from python.rl.runtime.world_batch.candidate_adapter import EpochReferenceFence
from python.rl.runtime.world_batch.candidate_adapter import EpochWorldRef
from python.rl.runtime.world_batch.candidate_adapter import episode_receipt_sha256
from tools.maintenance import runtime_kernel_candidate_caller_inventory as caller_inventory


ROOT = Path(__file__).resolve().parents[3]


def _world() -> EpochWorldRef:
    return EpochWorldRef((1, 2), (3, 4), 1, 0, 1)


def test_candidate_rejects_cross_host_and_stale_world_or_entity_refs() -> None:
    fence = EpochReferenceFence(_world())
    entity = fence.entity(17)
    assert fence.accepts_world(fence.world)
    assert fence.accepts_entity(entity)
    assert not fence.accepts_world(EpochWorldRef((9, 2), (3, 4), 1, 0, 1))
    assert not fence.accepts_entity(EpochEntityRef(fence.world, 17, 2))


def _identity(high: int, low: int) -> dict[str, int]:
    return {"high": high, "low": low}


def _episode(world: EpochWorldRef, episode_id: tuple[int, int], generation: int, *, world_generation: int | None = None) -> dict:
    return {
        "world": {
            "incarnation": {
                "host": {"host_id": _identity(*world.host_id), "boot_id": _identity(*world.boot_id)},
                "incarnation_epoch": world.incarnation_epoch,
            },
            "world_slot": world.world_slot,
            "world_generation": world.world_generation if world_generation is None else world_generation,
        },
        "episode_id": _identity(*episode_id),
        "episode_generation": generation,
    }


def _receipt(*, world: EpochWorldRef, kind: str, before: dict, after: dict, previous: int, resulting: int, phase: str, terminal: bool, reset: bool, barrier: int) -> dict:
    receipt = {
        "protocol_generation": 1,
        "kind": kind,
        "idempotency_key": _identity(10 + previous, 20 + resulting),
        "episode_before": before,
        "episode_after": after,
        "previous_step_sequence": previous,
        "resulting_step_sequence": resulting,
        "resulting_phase": phase,
        "terminal": terminal,
        "reset_applied": reset,
        "snapshot_id": _identity(30 + resulting, 40 + barrier),
        "snapshot_sha256": "a" * 64,
        "barrier_sequence": barrier,
        "receipt_sha256": "0" * 64,
    }
    receipt["receipt_sha256"] = episode_receipt_sha256(receipt)
    return receipt


def test_candidate_receipt_is_the_only_generation_update_authority() -> None:
    fence = EpochReferenceFence(_world())
    old_entity = fence.entity(17)
    before = _episode(fence.world, (5, 6), 1)
    terminal = _receipt(
        world=fence.world,
        kind="action",
        before=before,
        after=before,
        previous=0,
        resulting=1,
        phase="terminal",
        terminal=True,
        reset=False,
        barrier=0,
    )
    fence.apply_episode_receipt(terminal)
    reset = _receipt(
        world=fence.world,
        kind="reset",
        before=before,
        after=_episode(fence.world, (7, 8), 2, world_generation=2),
        previous=1,
        resulting=0,
        phase="running",
        terminal=False,
        reset=True,
        barrier=1,
    )
    fence.apply_episode_receipt(reset)
    assert fence.world.world_generation == 2
    assert not fence.accepts_entity(old_entity)
    assert fence.accepts_entity(fence.entity(17))


def test_candidate_receipt_rejects_forged_source_gap_and_digest() -> None:
    fence = EpochReferenceFence(_world())
    before = _episode(fence.world, (5, 6), 1)
    action = _receipt(
        world=fence.world,
        kind="action",
        before=before,
        after=before,
        previous=0,
        resulting=1,
        phase="running",
        terminal=False,
        reset=False,
        barrier=0,
    )
    forged = copy.deepcopy(action)
    forged["episode_before"]["world"]["incarnation"]["host"]["host_id"] = _identity(99, 1)
    forged["receipt_sha256"] = episode_receipt_sha256(forged)
    with pytest.raises(ValueError, match="source world"):
        fence.apply_episode_receipt(forged)
    gapped = copy.deepcopy(action)
    gapped["resulting_step_sequence"] = 3
    gapped["receipt_sha256"] = episode_receipt_sha256(gapped)
    with pytest.raises(ValueError, match="action receipt"):
        fence.apply_episode_receipt(gapped)
    with pytest.raises(ValueError, match="digest"):
        fence.apply_episode_receipt({**action, "snapshot_sha256": "b" * 64})
    with pytest.raises(ValueError, match="complete native mapping"):
        fence.apply_episode_receipt(object())


def test_candidate_receipt_replay_is_idempotent_and_key_reuse_is_rejected() -> None:
    fence = EpochReferenceFence(_world())
    before = _episode(fence.world, (5, 6), 1)
    action = _receipt(
        world=fence.world,
        kind="action",
        before=before,
        after=before,
        previous=0,
        resulting=1,
        phase="running",
        terminal=False,
        reset=False,
        barrier=0,
    )
    first = fence.apply_episode_receipt(action)
    assert fence.apply_episode_receipt(action) == first
    conflict = copy.deepcopy(action)
    conflict["snapshot_sha256"] = "b" * 64
    conflict["receipt_sha256"] = episode_receipt_sha256(conflict)
    with pytest.raises(ValueError, match="idempotency key"):
        fence.apply_episode_receipt(conflict)
    fence.acknowledge_receipt(action)
    with pytest.raises(ValueError, match="action receipt"):
        fence.apply_episode_receipt(action)


def test_candidate_world_identity_shape_is_strict() -> None:
    with pytest.raises(ValueError):
        EpochReferenceFence(EpochWorldRef(("x", "y"), (3, 4), 1, 0, 1))


def test_candidate_refs_fail_closed_on_invalid_values() -> None:
    with pytest.raises(ValueError):
        EpochReferenceFence(EpochWorldRef((0, 0), (3, 4), 1, 0, 1))
    fence = EpochReferenceFence(_world())
    with pytest.raises(ValueError):
        fence.entity(0)


def test_p4c_candidate_is_build_tree_only_and_not_a_production_authority() -> None:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    candidate_header = (
        ROOT / "src" / "runtime" / "host" / "integration" / "runtime_kernel_candidate.h"
    ).read_text(encoding="utf-8")
    facade_header = (
        ROOT / "src" / "runtime" / "host" / "integration" / "runtime_kernel_candidate_facade.h"
    ).read_text(encoding="utf-8")
    candidate_source = (
        ROOT / "src" / "runtime" / "host" / "integration" / "runtime_kernel_candidate.cpp"
    ).read_text(encoding="utf-8")
    assert "add_library(ef_runtime_kernel_candidate STATIC" in cmake
    assert "install(TARGETS ef_runtime_kernel_candidate" not in cmake
    assert "production_authorized = true" not in candidate_header
    assert "RuntimeHostCandidate" in candidate_header
    assert "RuntimeKernelCandidate &candidate" in facade_header
    assert "std::unique_ptr<RuntimeKernelCandidate>" not in facade_header
    assert "payload_sha256.front()" not in candidate_source
    assert "P4-C candidate plan is not bound to the sealed resolved composition" in candidate_source
    assert '"rl/runtime/world_batch/candidate_adapter.py"' in pyproject

    production_sources = [
        ROOT / "src" / "runtime" / "facade" / "runtime_facade.cpp",
        ROOT / "src" / "interfaces" / "python" / "bindings_runtime_facade.cpp",
    ]
    for source in production_sources:
        assert "runtime_kernel_candidate" not in source.read_text(encoding="utf-8")


def test_p4c_caller_inventory_is_fresh_and_has_no_maintained_callers() -> None:
    fixture = caller_inventory.load_fixture()
    caller_inventory.validate_inventory(fixture)
    assert fixture["classified_callers"]["build_tree_candidate"] == [
        "src/runtime/host/integration/runtime_kernel_candidate.cpp",
        "src/runtime/host/integration/runtime_kernel_candidate.h",
        "src/runtime/host/integration/runtime_kernel_candidate_facade.cpp",
        "src/runtime/host/integration/runtime_kernel_candidate_facade.h",
    ]
    assert fixture["classified_callers"]["test_only"] == [
        "src/tests/test_runtime_kernel_candidate.cpp",
        "src/tests/test_runtime_kernel_candidate_parity.cpp",
        "tests/architecture/runtime_host/test_runtime_kernel_candidate_contract.py",
    ]
    assert fixture["classified_callers"]["shadow_only"] == [
        "python/rl/runtime/world_batch/candidate_adapter.py",
    ]
    assert fixture["maintained_surface_violations"] == []
    assert fixture["classified_callers"]["unclassified"] == []


def test_p4c_caller_inventory_rejects_tampered_reference_sets() -> None:
    fixture = caller_inventory.load_fixture()
    forged = copy.deepcopy(fixture)
    forged["classified_callers"]["build_tree_candidate"].append("src/main.cpp")
    with pytest.raises(caller_inventory.InventoryError, match="stale"):
        caller_inventory.validate_inventory(forged)
