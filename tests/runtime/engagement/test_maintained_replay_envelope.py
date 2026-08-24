"""Real-run end-to-end proof for the T10 slice-5 maintained replay envelope (I69).

Slice 5 of the T10 evidence-spine census order (see
``docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md``
section 3) adds ``RuntimeFacade::build_maintained_replay_envelope``: a read-only
producer that assembles a WP15 ``ReplayEnvelope`` from the **real products of a
maintained run** instead of from the request/snapshot fields the two pre-existing
synthetic assemblies use.

The slice's whole thesis is "replace synthetic evidence with real run evidence",
so the companion ef_test suite
(``src/tests/test_runtime_facade_maintained_replay_envelope.cpp``) is not
sufficient on its own: it builds ``RuntimeWindowResult`` values by hand, which is
correct for pinning the fail-closed contract with exact allocator-cursor control
but is exactly the synthetic input this slice exists to eliminate. This file
supplies the missing half. Every envelope asserted here comes from an **actual
scenario** (the same seed-123 two-aircraft fire engagement the I59 slice-4 gates
run), driven through **actual maintained windows**
(``RuntimeFacadeAdapter.run_maintained_window`` over the real
``RuntimeFacade::run_window``), carrying **real exported packets** -- nothing
below hand-constructs a window product.

What is pinned:

* an admitted, validator-passing envelope over a genuinely run window, with every
  evidence field matched against the window product it was copied from;
* the adapter seam's opt-in contract: ``use_facade_evidence_producers=False``
  raises the named ``RuntimeError``, ``True`` over a real run succeeds;
* the missing-window error path (no window run, and explicit ``None`` evidence);
* post-return mutation of every producer-relevant public window field rejects at
  the sealed-evidence identity gate, before substituted evidence can reach a
  semantic gate;
* the census VA-2 snapshot-identity decision: the default ref is the packet's
  per-export string (byte-identical to the pre-slice value and provably NOT
  run-globally unique), and the opt-in qualification makes it unique additively;
* the default (non-opt-in) maintained path is unchanged and still carries the
  placeholder evidence, so nothing this slice adds perturbs existing output.

Gate boundary note: the binding remains ``def_rw`` for DTO compatibility, but a
mutation after ``run_window`` now fails the earlier sealed-evidence identity
gate. The lower semantic gates and post-assembly validator remain independently
pinned by C++ contract tests; Python must not bypass identity merely to reach
them.
"""

from __future__ import annotations

import math

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter  # noqa: E402

# The slice-4 (I59) gates already own a real seed-123 fire-engagement scenario
# driven entirely through the public adapter API. Reusing it keeps the two
# slices' "real run" identical rather than forking a second scenario definition
# that could drift.
from tests.runtime.engagement.test_trace_replay_wiring import _primed_adapter  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _run_fire_window  # noqa: E402


_RUN_ID = "run:maintained_replay_envelope"
_EPISODE_ID = "episode:maintained_replay_envelope"
# The real deterministic seed the scenario is set up with (setup.seeds = [123]).
_SEED = 123
_WINDOW_EVIDENCE_MISMATCH = (
    "maintained_replay_envelope_window_evidence_does_not_match_minted_window"
)


# --- Real-run fixtures ------------------------------------------------------


@pytest.fixture(scope="module")
def real_run() -> tuple[RuntimeFacadeAdapter, int, float]:
    """One opted-in adapter primed by really running the fire scenario.

    Module-scoped because priming steps the batch 80 times; each test then runs
    its own fresh maintained window against it, so no test observes another
    test's mutated window products.
    """
    return _primed_adapter(use_facade_evidence_producers=True)


def _real_window(real_run: tuple[RuntimeFacadeAdapter, int, float], tag: str) -> object:
    """Run one genuine maintained window and return its real evidence slice."""
    adapter, shooter_id, source_time_s = real_run
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, tag)
    # Guard the premise of every assertion in this file: this really is a run
    # product, not a fixture. A default-constructed window would have no
    # exported packets and no barrier trace.
    assert evidence.window_result is not None
    assert evidence.observation_packet is not None
    assert evidence.engagement_packet is not None
    assert evidence.barrier_trace, "a real maintained window records a barrier trace"
    assert evidence.executed_nodes, "a real maintained window records executed nodes"
    return evidence


def _build(
    real_run: tuple[RuntimeFacadeAdapter, int, float],
    evidence: object,
    **kwargs: object,
) -> object:
    adapter, _shooter_id, _source_time_s = real_run
    params: dict[str, object] = {
        "run_id": _RUN_ID,
        "episode_id": _EPISODE_ID,
        "deterministic_seed": _SEED,
        "window_evidence": evidence,
    }
    params.update(kwargs)
    return adapter.build_maintained_replay_envelope(**params)  # type: ignore[arg-type]


# --- The core evidence: an admitted envelope over a genuinely run window ----


def test_real_run_window_yields_an_admitted_validated_envelope(real_run) -> None:
    """The slice's thesis, proven on real evidence.

    A real maintained window's real products assemble an envelope that is
    admitted by the producer's own gates AND accepted by the independent
    fail-closed WP15 validator.
    """
    evidence = _real_window(real_run, "admitted")
    result = _build(real_run, evidence)

    assert result.admitted, (result.rejection_reason, list(result.errors))
    assert result.rejection_reason == ""
    assert list(result.errors) == []

    # The independent validator agrees -- not merely the producer's own gates.
    validation = ef_py.validate_replay_envelope(result.envelope)
    assert validation.valid is True
    assert list(validation.errors) == []


def test_every_envelope_field_traces_to_the_real_window_product(real_run) -> None:
    """Field-by-field: each envelope value equals the run product it came from.

    This is what separates "real evidence" from "plausible-looking evidence":
    every assertion's expected value is read back out of the window products
    rather than written as a literal.
    """
    evidence = _real_window(real_run, "fields")
    window_result = evidence.window_result
    result = _build(real_run, evidence)
    assert result.admitted
    envelope = result.envelope

    real_trace_ids = [int(value) for value in evidence.engagement_packet.trace_ids]
    assert real_trace_ids, "the opt-in path stamps a real minted trace id"
    anchor = real_trace_ids[-1]

    # Identity: the reserved namespace plus the caller-owned run identity.
    assert envelope.replay_envelope_id == f"replay:maintained:{_RUN_ID}:trace:{anchor}"
    assert envelope.run_id == _RUN_ID
    assert envelope.episode_id == _EPISODE_ID
    assert envelope.has_deterministic_seed is True
    assert int(envelope.deterministic_seed) == _SEED

    # Source time: the window's own real context time, not a re-derived clock.
    assert envelope.has_source_time is True
    assert envelope.source_time_s == pytest.approx(float(window_result.context.source_time_s))

    # Snapshot + facade provenance: copied from the real exported observation
    # packet's provenance struct.
    real_provenance = evidence.observation_packet.provenance
    assert envelope.snapshot_ref.snapshot_version_ref == str(
        list(real_provenance.source_observation_versions)[0]
    )
    assert envelope.facade_provenance_ref.packet_ref == str(
        list(real_provenance.observation_packet_ids)[0]
    )
    assert envelope.facade_provenance_ref.packet_kind == "ObservationBatchPacket"
    assert list(
        envelope.facade_provenance_ref.information_state_source.observation_packet_ids
    ) == list(real_provenance.observation_packet_ids)
    assert (
        envelope.facade_provenance_ref.information_state_source.source_label
        == real_provenance.source_label
    )

    # Barrier: the real window_commit record out of the window's own trace.
    real_commits = [
        record for record in evidence.barrier_trace if record.barrier_id == "window_commit"
    ]
    assert real_commits, "a real maintained window commits"
    assert envelope.barrier_ref.barrier_id == "window_commit"
    assert int(envelope.barrier_ref.barrier_sequence) == int(real_commits[-1].sequence)
    assert envelope.barrier_ref.barrier_detail == evidence.engagement_packet.barrier_detail

    # Event order: anchored on the real minted trace id and the real export node.
    assert envelope.event_order_ref.sort_key == "timestamp_priority_event_id"
    assert envelope.event_order_ref.event_id == f"event:trace:{anchor}"
    assert envelope.event_order_ref.producer_node_id == (
        evidence.engagement_packet.producer_node_id
    )

    # Honest restore claim: the maintained path registers no worldline snapshot.
    assert envelope.snapshot_restore_supported is False
    assert envelope.restore_support_boundary == ("restore_unsupported_until_snapshot_restore_proof")

    # Evidence refs: producer label first, then the canonical ordered refs.
    assert list(result.evidence_refs) == [
        "RuntimeFacade.build_maintained_replay_envelope",
        f"snapshot_version_ref={envelope.snapshot_ref.snapshot_version_ref}",
        "barrier_id=window_commit",
        f"event_order_ref=event:trace:{anchor}",
        f"facade_provenance_ref={envelope.facade_provenance_ref.packet_ref}",
        "composition_evidence_sha256="
        f"{real_run[0].facade.export_composition_evidence().evidence.evidence_sha256}",
    ]


def test_real_run_envelope_tracks_the_run_minted_trace_id_across_windows(real_run) -> None:
    """Successive real windows produce distinct envelopes keyed by real evidence.

    The envelope id advances because the run's VA-8 allocator advances -- the
    envelope identity is bound to produced evidence, not to a call counter.
    """
    ids: list[str] = []
    anchors: list[int] = []
    for k in range(3):
        evidence = _real_window(real_run, f"sequence:{k}")
        result = _build(real_run, evidence)
        assert result.admitted, result.rejection_reason
        ids.append(result.envelope.replay_envelope_id)
        anchors.append(int(list(evidence.engagement_packet.trace_ids)[-1]))

    assert len(set(ids)) == 3, ids
    # Strictly increasing real minted ids, and each envelope id embeds its own.
    assert anchors == sorted(anchors)
    assert len(set(anchors)) == 3
    for envelope_id, anchor in zip(ids, anchors):
        assert envelope_id.endswith(f":trace:{anchor}")


def test_producer_mints_nothing_over_a_real_run(real_run) -> None:
    """The producer is read-only: a real run's cursors are untouched by it."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "readonly")
    trace_cursor = int(adapter.facade.peek_next_trace_id())
    snapshot_cursor = int(adapter.facade.peek_next_run_snapshot_version())

    first = _build(real_run, evidence)
    second = _build(real_run, evidence)

    assert first.admitted and second.admitted
    assert first.envelope.replay_envelope_id == second.envelope.replay_envelope_id
    assert list(first.evidence_refs) == list(second.evidence_refs)
    # Building an envelope twice consumed no evidence identity.
    assert int(adapter.facade.peek_next_trace_id()) == trace_cursor
    assert int(adapter.facade.peek_next_run_snapshot_version()) == snapshot_cursor


# --- The adapter seam's opt-in contract ------------------------------------


def test_seam_requires_the_optin_evidence_producers() -> None:
    """``use_facade_evidence_producers=False`` raises the named RuntimeError.

    Load-bearing: the default path's placeholder ``trace_ids = [1]`` would be
    rejected by the C++ producer anyway, but the seam refuses *before* that so
    the caller gets a message naming the switch rather than an opaque
    rejection_reason. Asserted without priming a run: the guard precedes any
    window lookup.
    """
    adapter = RuntimeFacadeAdapter(1)
    assert adapter.use_facade_evidence_producers is False

    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True") as exc:
        adapter.build_maintained_replay_envelope(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )
    message = str(exc.value)
    assert "maintained replay envelope" in message
    assert "placeholder" in message


def test_seam_requires_a_completed_window(real_run) -> None:
    """The missing-window error path.

    ``window_evidence=None`` is the sentinel for "use the run's last window"
    (pinned by :func:`test_seam_defaults_to_the_last_real_window`), so the error
    fires when there is genuinely no window to use: a fresh opted-in adapter
    that has never run one, and a run whose stored evidence was cleared.
    """
    adapter, _shooter_id, _source_time_s = real_run

    # A fresh opted-in adapter that has never run a window: no stored evidence.
    fresh = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
    assert fresh.last_window_evidence is None
    with pytest.raises(RuntimeError, match=r"completed maintained window"):
        fresh.build_maintained_replay_envelope(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )

    # A real run whose window evidence has been cleared: same named error, so the
    # seam cannot silently reuse a stale window after an explicit clear.
    _real_window(real_run, "cleared")
    adapter.clear_last_window_evidence()
    assert adapter.last_window_evidence is None
    with pytest.raises(RuntimeError, match=r"completed maintained window"):
        adapter.build_maintained_replay_envelope(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )


def test_seam_defaults_to_the_last_real_window(real_run) -> None:
    """Omitting ``window_evidence`` uses the run's own most recent real window."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "implicit")
    assert adapter.last_window_evidence is evidence

    implicit = adapter.build_maintained_replay_envelope(
        run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
    )
    explicit = _build(real_run, evidence)
    assert implicit.admitted and explicit.admitted
    assert implicit.envelope.replay_envelope_id == explicit.envelope.replay_envelope_id


# --- Negative gates: caller identity plus sealed-evidence rejection ----------
#
# Each mutation starts from a REAL run window. The token binds the exact evidence
# returned by run_window, so a passing case proves substituted public DTO fields
# cannot borrow that genuine token.


def test_gate_run_id_required(real_run) -> None:
    evidence = _real_window(real_run, "gate:run_id")
    result = _build(real_run, evidence, run_id="   ")
    assert result.admitted is False
    assert result.rejection_reason == "maintained_replay_envelope_run_id_required"


def test_gate_episode_id_required(real_run) -> None:
    evidence = _real_window(real_run, "gate:episode_id")
    result = _build(real_run, evidence, episode_id="")
    assert result.admitted is False
    assert result.rejection_reason == "maintained_replay_envelope_episode_id_required"


def test_mutated_observation_packet_provenance_is_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:provenance")
    # Drop the real exported provenance ids; everything else stays real.
    evidence.window_result.observation_packet.provenance.observation_packet_ids = []
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_mutated_observation_packet_versions_are_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:versions")
    evidence.window_result.observation_packet.provenance.source_observation_versions = []
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_mutated_engagement_trace_ids_are_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:trace_missing")
    evidence.window_result.engagement_packet.trace_ids = []
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_substituted_unminted_trace_id_cannot_borrow_a_genuine_token(real_run) -> None:
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "gate:trace_foreign")
    real_ids = [int(value) for value in evidence.window_result.engagement_packet.trace_ids]
    cursor = int(adapter.facade.peek_next_trace_id())
    assert all(1 <= value < cursor for value in real_ids), (real_ids, cursor)

    # An id exactly at the cursor was never handed out by this run.
    evidence.window_result.engagement_packet.trace_ids = real_ids + [cursor]
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH
    # Rejection leaks no partially assembled evidence.
    assert result.envelope.replay_envelope_id == ""
    assert list(result.evidence_refs) == []


def test_mutated_window_commit_barrier_is_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:barrier")
    real_trace = list(evidence.window_result.barrier_trace)
    assert any(record.barrier_id == "window_commit" for record in real_trace)
    # Keep every other real barrier record; remove only window_commit.
    evidence.window_result.barrier_trace = [
        record for record in real_trace if record.barrier_id != "window_commit"
    ]
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_mutated_engagement_producer_node_is_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:producer")
    assert evidence.window_result.engagement_packet.producer_node_id
    evidence.window_result.engagement_packet.producer_node_id = ""
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_mutated_source_time_is_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:time")
    assert math.isfinite(float(evidence.window_result.context.source_time_s))
    evidence.window_result.context.source_time_s = float("nan")
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


def test_gate_run_snapshot_version_not_minted_by_this_run(real_run) -> None:
    """The ninth gate (I69 VA-2): the qualification value must be run-minted."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "gate:run_snapshot")
    cursor = int(adapter.facade.peek_next_run_snapshot_version())

    # Go through the facade directly: the adapter recovers the value from real
    # window products and so cannot express an unminted one -- which is the
    # point of the gate, but the gate itself still needs proving.
    result = adapter.facade.build_maintained_replay_envelope(
        evidence.window_result, _RUN_ID, _EPISODE_ID, _SEED, cursor
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_replay_envelope_run_snapshot_version_not_minted_by_this_run"
    )
    assert result.envelope.snapshot_ref.snapshot_version_ref == ""


def test_gate_allocated_but_unrecorded_snapshot_version_is_rejected(real_run) -> None:
    """Allocator membership is insufficient without this window recording the version."""
    adapter, _shooter_id, _source_time_s = real_run
    allocated_without_window = int(adapter.facade.allocate_run_snapshot_version())
    evidence = _real_window(real_run, "gate:run_snapshot_allocated_without_window")

    result = adapter.facade.build_maintained_replay_envelope(
        evidence.window_result,
        _RUN_ID,
        _EPISODE_ID,
        _SEED,
        allocated_without_window,
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_replay_envelope_run_snapshot_version_not_minted_by_this_run"
    )
    assert result.envelope.snapshot_ref.snapshot_version_ref == ""
    assert list(result.evidence_refs) == []


# --- Census VA-2: the snapshot-identity decision ---------------------------


def test_default_snapshot_ref_is_the_packets_per_export_value_and_is_not_unique(
    real_run,
) -> None:
    """Documents the VA-2 limitation the default ref carries, on real evidence.

    The default ``snapshot_version_ref`` is the observation packet's own
    run-produced provenance string. It is real, but ``packet.snapshot_version``
    is the per-export sequence that resets every export, so several real exports
    of the SAME run produce the SAME ref -- the envelope's snapshot identity does
    not distinguish them. This test pins that fact rather than hiding it, and
    locks the default's serialized value against drift.
    """
    refs: list[str] = []
    for k in range(3):
        evidence = _real_window(real_run, f"va2:default:{k}")
        result = _build(real_run, evidence)
        assert result.admitted
        # Exactly the packet's own string -- nothing added by default.
        assert result.envelope.snapshot_ref.snapshot_version_ref == str(
            list(evidence.observation_packet.provenance.source_observation_versions)[0]
        )
        refs.append(result.envelope.snapshot_ref.snapshot_version_ref)

    assert all(ref.startswith("global:") for ref in refs)
    # The census VA-2 defect, demonstrated rather than asserted in prose: three
    # distinct real exports, one indistinguishable snapshot identity.
    assert len(set(refs)) == 1, refs


def test_optin_qualification_makes_the_snapshot_ref_run_globally_unique(real_run) -> None:
    """The VA-2 fix: opt-in, additive, and unique across real exports."""
    pairs: list[tuple[str, str]] = []
    for k in range(3):
        evidence = _real_window(real_run, f"va2:optin:{k}")
        default = _build(real_run, evidence)
        qualified = _build(real_run, evidence, qualify_run_global_snapshot_version=True)
        assert default.admitted and qualified.admitted, qualified.rejection_reason

        default_ref = default.envelope.snapshot_ref.snapshot_version_ref
        qualified_ref = qualified.envelope.snapshot_ref.snapshot_version_ref
        # Additive by construction: the pre-existing value keeps its exact
        # meaning and position as the prefix; the run-global part is appended.
        assert qualified_ref.startswith(default_ref)
        assert qualified_ref[len(default_ref) :].startswith(":run_snapshot:")
        # The appended value is the run's own minted version, recovered from the
        # window's real executed-node records -- not a caller-invented number.
        recovered = qualified_ref.rsplit(":run_snapshot:", 1)[1]
        real_node_versions = {str(node.source_snapshot_version) for node in evidence.executed_nodes}
        assert f"snapshot:{recovered}" in real_node_versions

        # Still a valid envelope under the independent validator.
        assert ef_py.validate_replay_envelope(qualified.envelope).valid is True
        pairs.append((default_ref, qualified_ref))

    # The point of the fix: the default refs collide, the qualified ones do not.
    assert len({default_ref for default_ref, _ in pairs}) == 1
    assert len({qualified_ref for _, qualified_ref in pairs}) == 3


# --- The default (non-opt-in) path is unchanged -----------------------------


def test_default_maintained_path_still_carries_the_placeholder_evidence() -> None:
    """The additive red line: the non-opt-in run is untouched by this slice.

    A default adapter runs the same real scenario and still produces the
    pre-slice placeholder evidence, with both run-global cursors never advanced
    -- so nothing slice 5 added can have perturbed a default-path serialized
    value. (The I59 gates own this invariant for slice 4; re-pinned here at the
    slice-5 baseline because slice 5 touches the same adapter.)
    """
    adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, "slice5:default")

    assert [int(value) for value in evidence.engagement_packet.trace_ids] == [1]
    assert int(adapter.facade.peek_next_trace_id()) == 1
    assert int(adapter.facade.peek_next_run_snapshot_version()) == 1

    # And the envelope seam stays shut on this path.
    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True"):
        adapter.build_maintained_replay_envelope(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )


def test_default_path_placeholder_evidence_is_inadmissible_to_the_producer() -> None:
    """Why the seam's opt-in requirement is not merely policy.

    Reaching past the adapter seam straight to the C++ producer with a real
    DEFAULT-path window shows the producer independently fail-closes: the
    placeholder ``trace_ids = [1]`` was not minted by this run's allocator
    (whose cursor is still 1), so no synthetic-evidence envelope can be admitted
    even by a caller that bypasses the adapter guard.
    """
    adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, "slice5:inadmissible")
    assert [int(value) for value in evidence.engagement_packet.trace_ids] == [1]
    assert int(adapter.facade.peek_next_trace_id()) == 1

    result = adapter.facade.build_maintained_replay_envelope(
        evidence.window_result, _RUN_ID, _EPISODE_ID, _SEED
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_replay_envelope_trace_ids_not_minted_by_this_run"
    )
