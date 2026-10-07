from __future__ import annotations

import pytest

from python.tasking_contracts.common.command_link import ScriptedCommandLink


def _link(seed: int = 19) -> ScriptedCommandLink:
    return ScriptedCommandLink(
        active_node_ids=("lead", "wing", "reserve"),
        command_edges=(("lead", "wing"), ("reserve", "wing")),
        seed=seed,
    )


def _send(link: ScriptedCommandLink, **kwargs):
    return link.send(
        source_node_id="lead",
        target_node_id="wing",
        payload=("opaque",),
        clock_s=kwargs.pop("clock_s", 0.0),
        **kwargs,
    )


def test_default_delay_preserves_order_and_opaque_payload_identity() -> None:
    link = _link()
    later = _send(link, delay_s=0.3)
    first = _send(link, delay_s=0.1 + 0.2)
    earliest = _send(link, delay_s=0.1)
    assert link.deliver(clock_s=0.05) == ()
    assert link.deliver(clock_s=0.3) == (earliest, later, first)
    assert later.expires_at_s is None
    assert link.counts == {"queued": 3, "delivered": 3}
    assert link.pending == ()


@pytest.mark.parametrize("delay_s", [0.2, 1.0])
def test_expiration_wins_at_exact_boundary_even_before_delivery(delay_s: float) -> None:
    link = _link()
    _send(link, delay_s=delay_s, ttl_s=0.2)
    assert link.deliver(clock_s=0.2) == ()
    assert link.pending == ()
    assert link.counts == {"queued": 1, "expired": 1}
    assert link.receipts[-1].clock_s == 0.2


def test_loss_is_seeded_and_reset_replays_receipts() -> None:
    link = _link()

    def run():
        for _ in range(32):
            _send(link, drop_prob=0.5)
        delivered = link.deliver(clock_s=0.0)
        return delivered, link.receipts, link.counts

    first = run()
    assert 0 < first[2]["dropped"] < 32
    assert first[2]["delivered"] + first[2]["dropped"] == 32
    link.reset()
    assert link.counts == {}
    assert link.receipts == ()
    assert run() == first
    other = _link(seed=20)
    for _ in range(32):
        _send(other, drop_prob=0.5)
    other.deliver(clock_s=0.0)
    assert other.receipts != first[1]


@pytest.mark.parametrize("failed_node", ["lead", "wing"])
def test_unavailable_node_cancels_pending_and_restore_requires_new_send(failed_node: str) -> None:
    link = _link()
    _send(link, delay_s=1.0)
    link.set_node_available(failed_node, available=False, clock_s=0.1)
    assert link.counts == {"queued": 1, "cancelled": 1}
    with pytest.raises(KeyError, match="active graph nodes"):
        _send(link, clock_s=0.1)
    link.set_node_available(failed_node, available=True, clock_s=0.2)
    assert link.deliver(clock_s=1.0) == ()
    replacement = _send(link, clock_s=1.0)
    assert link.deliver(clock_s=1.0) == (replacement,)


def test_leader_loss_keeps_unrelated_reassignment_delivery() -> None:
    link = _link()
    _send(link, delay_s=1.0)
    replacement = link.send(
        source_node_id="reserve",
        target_node_id="wing",
        payload=("replacement",),
        clock_s=0.0,
        delay_s=1.0,
    )
    link.set_node_available("lead", available=False, clock_s=0.1)
    assert link.deliver(clock_s=1.0) == (replacement,)
    assert link.counts == {"queued": 2, "cancelled": 1, "delivered": 1}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"delay_s": -1},
        {"delay_s": float("inf")},
        {"clock_s": float("nan")},
        {"ttl_s": 0},
        {"ttl_s": -1},
        {"drop_prob": -0.1},
        {"drop_prob": 1.1},
        {"clock_s": 1e308, "delay_s": 1e308},
    ],
)
def test_bad_transport_settings_do_not_queue_or_advance_state(kwargs: dict) -> None:
    link = _link()
    with pytest.raises(ValueError):
        _send(link, **kwargs)
    assert link.pending == link.receipts == ()
    assert _send(link).sequence == 1


def test_authority_clock_and_close_fail_closed() -> None:
    link = _link()
    with pytest.raises(ValueError, match="undeclared command edge"):
        link.send(source_node_id="wing", target_node_id="lead", payload=(), clock_s=0.0)
    _send(link, clock_s=1.0)
    with pytest.raises(ValueError, match="backwards"):
        link.deliver(clock_s=0.5)
    link.close()
    assert link.pending == ()
    with pytest.raises(RuntimeError, match="closed"):
        link.reset()
    with pytest.raises(RuntimeError, match="closed"):
        link.deliver(clock_s=1.0)


def test_receipts_are_bounded_but_totals_and_instances_are_isolated() -> None:
    link, other = _link(), _link()
    for _ in range(300):
        _send(link, drop_prob=1.0)
    assert len(link.receipts) == 256
    assert link.counts == {"dropped": 300}
    assert other.pending == other.receipts == ()
    assert other.counts == {}
    link.reset(seed=41)
    assert _send(link).sequence == 1
