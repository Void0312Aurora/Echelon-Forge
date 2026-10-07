from __future__ import annotations

import json

import numpy as np
import pytest

from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.tasking_contracts.air.ew.formation import AirFormationEWRuntime
from tests.runtime.multi_agent.test_cooperative_vec_env_tasking import (
    _cooperative_cruise_scenario,
)


def _action(rows: int = 2) -> np.ndarray:
    actions = np.zeros((rows, 16), dtype=np.float32)
    actions[:, 3] = 0.7
    actions[:, 12:16] = (1.0, 1.0, 1.0, 1.0)
    return actions


def _env(tmp_path, *, worlds: int = 1, commanders=("Lead", "Wing")):
    scenario = tmp_path / "formation_ew.json"
    payload = _cooperative_cruise_scenario()
    payload["meta"]["max_steps"] = 200
    scenario.write_text(json.dumps(payload), encoding="utf-8")
    env = CooperativeWorldBatchVecEnv(
        scenario_path=str(scenario),
        n_envs=worlds,
        action_mode="air_ew_hybrid_v2",
        include_ew_state=True,
        ew_formation_commanders=commanders,
        worker_threads=1,
    )
    env.seed(20261007)
    env.reset()
    return env


def test_role_orders_are_authorized_seeded_expiring_and_reassign_on_leader_loss():
    runtime = AirFormationEWRuntime(
        member_ids=("Lead", "Wing"), commander_ids=("Lead", "Wing"), seed=31
    )
    action = _action(1)[0]

    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.0,
        delay_s=0.3,
        ttl_s=0.2,
    )
    runtime.advance(clock_s=0.2)
    assert runtime.filter_action("Wing", action)[14] == 0.0
    assert runtime.link.counts["expired"] == 1

    with pytest.raises(ValueError, match="current commander"):
        runtime.issue(
            source_member_id="Wing",
            target_member_id="Lead",
            role_id="self_protect",
            clock_s=0.2,
        )
    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.2,
        ttl_s=2.0,
    )
    runtime.advance(clock_s=0.2)
    assert runtime.filter_action("Wing", action)[14] == 1.0
    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.2,
        delay_s=1.0,
        ttl_s=2.0,
    )
    runtime.set_member_available("Lead", available=False, clock_s=0.3)
    assert runtime.leader_id == "Wing"
    assert runtime.link.counts["cancelled"] == 1
    assert runtime.filter_action("Wing", action)[14] == 0.0
    assert runtime.receipts[-1].outcome == "revoked_authority"

    runtime.issue(
        source_member_id="Wing",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.3,
        ttl_s=1.0,
    )
    runtime.advance(clock_s=0.3)
    assert runtime.filter_action("Wing", action)[14] == 1.0
    runtime.advance(clock_s=1.3)
    assert runtime.filter_action("Wing", action)[14] == 0.0
    assert runtime.receipts[-1].outcome == "expired_lease"

    runtime.set_member_available("Wing", available=False, clock_s=1.3)
    runtime.set_member_available("Lead", available=True, clock_s=1.4)
    assert runtime.leader_id == "Lead"
    with pytest.raises(ValueError, match="current commander"):
        runtime.issue(
            source_member_id="Wing",
            target_member_id="Lead",
            role_id="self_protect",
            clock_s=1.4,
        )
    runtime.close()


def test_loss_and_seeded_role_receipts_replay_exactly():
    def run(seed):
        runtime = AirFormationEWRuntime(
            member_ids=("Lead", "Wing"), commander_ids=("Lead",), seed=seed
        )
        for tick in range(16):
            runtime.issue(
                source_member_id="Lead",
                target_member_id="Wing",
                role_id="self_protect",
                clock_s=tick * 0.1,
                drop_prob=0.5,
            )
            runtime.advance(clock_s=tick * 0.1)
        result = runtime.snapshot("Wing")
        runtime.close()
        return result

    first = run(44)
    assert first == run(44)
    assert first != run(45)
    assert first["link_counts"]["dropped"] > 0


def test_cooperative_env_scopes_roles_by_world_and_preserves_local_countermeasures(tmp_path):
    env = _env(tmp_path, worlds=2)
    try:
        actions = _action(rows=4)
        actions[[0, 2], 13] = 0.0
        actions[[1, 3], 12] = 0.0
        observations, _, _, _ = env.step(actions)
        assert observations["ew_state"].shape == (4, 6)
        assert not bool(env._slots[1].last_inst.jammer_transmitting)
        assert not bool(env._slots[3].last_inst.jammer_transmitting)

        resources_before = [
            (
                int(slot.last_inst.countermeasure_chaff_remaining),
                int(slot.last_inst.countermeasure_flare_remaining),
            )
            for slot in env._slots
        ]
        env.send_ew_role_order(
            source_member_id="Lead",
            target_member_id="Wing",
            role_id="self_protect",
            world_index=0,
            ttl_s=3.0,
        )
        env.send_ew_role_order(
            source_member_id="Lead",
            target_member_id="Wing",
            role_id="emission_hold",
            world_index=1,
            ttl_s=3.0,
        )
        for _ in range(40):
            observations, _, dones, infos = env.step(actions)
            assert not dones.any()

        assert bool(env._slots[1].last_inst.jammer_transmitting)
        assert not bool(env._slots[3].last_inst.jammer_transmitting)
        assert infos[1]["air_ew_formation"]["role_id"] == "self_protect"
        assert infos[3]["air_ew_formation"]["role_id"] == "emission_hold"
        for index in range(4):
            inst = env._slots[index].last_inst
            if index % 2 == 0:
                assert int(inst.countermeasure_chaff_remaining) < resources_before[index][0]
                assert int(inst.countermeasure_flare_remaining) == resources_before[index][1]
            else:
                assert int(inst.countermeasure_flare_remaining) < resources_before[index][1]
                assert int(inst.countermeasure_chaff_remaining) == resources_before[index][0]
        np.testing.assert_array_equal(observations["ew_state"][:, 3], [0, 1, 0, 0])
    finally:
        env.close()


def test_cooperative_env_cancels_stale_order_on_leader_loss_and_resets_roles(tmp_path):
    env = _env(tmp_path)
    try:
        actions = _action()
        env.step(actions)
        env.send_ew_role_order(
            source_member_id="Lead",
            target_member_id="Wing",
            role_id="self_protect",
            delay_s=1.0,
            ttl_s=2.0,
        )
        env.set_ew_member_available("Lead", available=False)
        assert env._ew_runtime(0).leader_id == "Wing"
        with pytest.raises(ValueError, match="current commander"):
            env.send_ew_role_order(
                source_member_id="Lead", target_member_id="Wing", role_id="self_protect"
            )
        env.step(actions)
        assert not bool(env._slots[1].last_inst.jammer_transmitting)

        env.send_ew_role_order(
            source_member_id="Wing", target_member_id="Wing", role_id="self_protect", ttl_s=2.0
        )
        env.step(actions)
        assert bool(env._slots[1].last_inst.jammer_transmitting)
        env.reset()
        env.step(actions)
        assert not bool(env._slots[1].last_inst.jammer_transmitting)
    finally:
        env.close()


@pytest.mark.parametrize(
    "drop_prob,expected",
    [(0.0, [False, False, True, True, False]), (1.0, [False] * 5)],
)
def test_cooperative_delivery_delay_expiry_and_loss_reach_native_state(
    tmp_path, drop_prob, expected
):
    env = _env(tmp_path)
    try:
        env.send_ew_role_order(
            source_member_id="Lead",
            target_member_id="Wing",
            role_id="self_protect",
            delay_s=0.1,
            ttl_s=0.2,
            drop_prob=drop_prob,
        )
        trace = []
        for _ in expected:
            env.step(_action())
            trace.append(bool(env._slots[1].last_inst.jammer_transmitting))
            assert not bool(env._slots[0].last_inst.jammer_transmitting)
        assert trace == expected
    finally:
        env.close()


def test_older_delayed_role_cannot_overwrite_newer_hold_or_survive_authority_epoch():
    runtime = AirFormationEWRuntime(member_ids=("Lead", "Wing"), commander_ids=("Lead", "Wing"))
    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.0,
        delay_s=0.3,
        ttl_s=2.0,
    )
    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="emission_hold",
        clock_s=0.1,
        ttl_s=2.0,
    )
    runtime.advance(clock_s=0.1)
    runtime.advance(clock_s=0.3)
    assert runtime.snapshot("Wing")["role_id"] == "emission_hold"
    assert runtime.receipts[-1].outcome == "rejected_older_order"
    runtime.set_member_available("Lead", available=False, clock_s=0.4)
    runtime.issue(
        source_member_id="Wing",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.4,
        delay_s=0.5,
        ttl_s=2.0,
    )
    runtime.set_member_available("Lead", available=True, clock_s=0.5)
    runtime.set_member_available("Lead", available=False, clock_s=0.6)
    runtime.advance(clock_s=0.9)
    assert runtime.filter_action("Wing", _action(1)[0])[14] == 0.0
    assert runtime.receipts[-1].outcome == "rejected_authority"
    runtime.close()


@pytest.mark.parametrize(
    "kwargs",
    [{"role_id": "escort_jammer"}, {"ttl_s": None}, {"ttl_s": 0.0}, {"ttl_s": float("inf")}],
)
def test_unsupported_role_and_unbounded_lifetime_are_denied(kwargs):
    runtime = AirFormationEWRuntime(member_ids=("Lead", "Wing"), commander_ids=("Lead",))
    options = {
        "source_member_id": "Lead",
        "target_member_id": "Wing",
        "role_id": "self_protect",
        "clock_s": 0.0,
    }
    options.update(kwargs)
    with pytest.raises(ValueError):
        runtime.issue(**options)
    assert runtime.link.pending == ()
    runtime.close()


def test_role_filter_preserves_combat_and_countermeasure_prefix_and_does_not_mutate_policy():
    runtime = AirFormationEWRuntime(member_ids=("Lead", "Wing"), commander_ids=("Lead",))
    action = np.arange(16, dtype=np.float32)
    filtered = runtime.filter_action("Wing", action)
    np.testing.assert_array_equal(filtered[:14], action[:14])
    np.testing.assert_array_equal(filtered[14:], [0, 0])
    np.testing.assert_array_equal(action, np.arange(16, dtype=np.float32))
    runtime.close()


def test_unconfigured_cooperative_path_keeps_existing_jammer_requests(tmp_path):
    env = _env(tmp_path, commanders=None)
    try:
        env.step(_action())
        assert all(bool(slot.last_inst.jammer_transmitting) for slot in env._slots)
        with pytest.raises(RuntimeError, match="enabled"):
            env.send_ew_role_order(
                source_member_id="Lead", target_member_id="Wing", role_id="self_protect"
            )
    finally:
        env.close()


def test_cooperative_role_receipts_and_native_ew_state_replay_on_seeded_reset(tmp_path):
    env = _env(tmp_path)
    try:
        traces = []
        for _ in range(2):
            env.seed(20261007)
            env.reset()
            trace = []
            for tick in range(8):
                env.send_ew_role_order(
                    source_member_id="Lead",
                    target_member_id="Wing",
                    role_id="self_protect",
                    delay_s=0.05,
                    ttl_s=0.1,
                    drop_prob=0.5,
                )
                obs, _, dones, infos = env.step(_action())
                assert not dones.any()
                trace.append((obs["ew_state"].tolist(), infos[1]["air_ew_formation"]))
            traces.append(trace)
        assert traces[0] == traces[1]
    finally:
        env.close()


def test_member_loss_revokes_accepted_lease_and_restoration_needs_new_order():
    runtime = AirFormationEWRuntime(member_ids=("Lead", "Wing"), commander_ids=("Lead",))
    runtime.issue(
        source_member_id="Lead",
        target_member_id="Wing",
        role_id="self_protect",
        clock_s=0.0,
    )
    runtime.advance(clock_s=0.0)
    assert runtime.filter_action("Wing", _action(1)[0])[14] == 1
    runtime.set_member_available("Wing", available=False, clock_s=0.1)
    assert runtime.receipts[-1].outcome == "revoked_member"
    runtime.set_member_available("Wing", available=True, clock_s=0.2)
    assert runtime.filter_action("Wing", _action(1)[0])[14] == 0
    runtime.close()


@pytest.mark.parametrize("commanders", [(), "Lead"])
def test_bad_formation_configuration_is_rejected_before_opening_world(tmp_path, commanders):
    with pytest.raises(ValueError, match="ew_formation_commanders"):
        CooperativeWorldBatchVecEnv(
            scenario_path=str(tmp_path / "missing.json"),
            n_envs=1,
            action_mode="air_ew_hybrid_v2",
            ew_formation_commanders=commanders,
        )


def test_formation_mode_requires_v2_and_declared_commanders(tmp_path):
    with pytest.raises(ValueError, match="air_ew_hybrid_v2"):
        CooperativeWorldBatchVecEnv(
            scenario_path=str(tmp_path / "missing.json"),
            n_envs=1,
            action_mode="air_ew_hybrid_v1",
            ew_formation_commanders=("Lead",),
        )
    with pytest.raises(ValueError, match="controlled member roster"):
        AirFormationEWRuntime(member_ids=("Lead", "Wing"), commander_ids=("Unknown",))
