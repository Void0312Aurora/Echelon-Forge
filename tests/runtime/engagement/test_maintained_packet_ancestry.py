"""Real-run end-to-end proof for the T10 slice-6A maintained packet ancestry.

Slice 6A of the T10 evidence-spine census order (see
``docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md``
section 3 step 6) adds ``RuntimeFacade::build_maintained_packet_ancestry``: a
read-only producer that populates packet ancestry for the engagement-event
packet family -- ``parent_trace_id`` linkage minted from the run's own VA-8
trace allocator plus a typed ``*_ref`` lineage -- from the **real products of a
maintained run**, never mutating the default export path in place.

Every admitted ancestry asserted here comes from an **actual scenario** (the
same seed-123 two-aircraft fire engagement the I59 slice-4 gates run), driven
through **actual maintained windows**
(``RuntimeFacadeAdapter.run_maintained_window`` over the real
``RuntimeFacade::run_window``), carrying **real exported packets**.

What is pinned:

* an end-to-end ancestry chain across successive real windows, each link the
  previous window's genuinely minted VA-8 anchor;
* replay validation: an admitted ancestry always names the same window's
  admitted maintained replay envelope, and that envelope passes the independent
  fail-closed WP15 validator;
* the retained/default byte-parity red line: the producer returns parent-linked
  COPIES (the stored window products keep ``parent_trace_id = 0``), mints
  nothing (both run-global cursors are untouched by building ancestry), and the
  default (non-opt-in) maintained path still carries the placeholder evidence
  with all exported trace parents at the pre-slice default ``0``;
* fail-closed identity/evidence handling: window evidence produced by a
  DIFFERENT facade is rejected by the opaque window/facade identity gate,
  post-return mutation is rejected by the sealed-evidence gate, an allocated
  but unrecorded parent id is rejected, and
  a parent that does not strictly precede the window's own tags is rejected --
  each with a named reason and with no partially assembled lineage leaked;
* the seam's opt-in contract: ``use_facade_evidence_producers=False`` raises the
  named ``RuntimeError`` before any window lookup (I59 discipline).

Build-surface note (this iteration): C++ compilation happens at landing, so the
binding-dependent tests below skip -- loudly, via ``_requires_binding`` -- when
the local ``ef_py`` build predates the slice-6A surface. Landing MUST
compile-verify and re-run this file expecting zero ``_requires_binding`` skips
(the only remaining skip is ``test_seam_names_the_missing_slice6a_binding``,
which is reachable only on a pre-slice-6A build by construction); the
seam-guard and default-parity tests run on any build.

Smoke registration: deliberately not added to ``tests/smoke/ci_smoke_suite.json``,
matching the slice-4/slice-5 precedent (``test_trace_replay_wiring.py`` /
``test_maintained_replay_envelope.py`` are likewise excluded): these are real
engine runs priming an 80-step scenario per adapter, and the default-path
serialized surface they guard is already smoke-pinned by
``test_trace_replay_gates.py``.
"""

from __future__ import annotations

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter  # noqa: E402

# The slice-4 (I59) gates own the real seed-123 fire-engagement scenario driven
# entirely through the public adapter API; slice 5 (I69) reuses it for the same
# reason this file does: one shared "real run" definition that cannot fork.
from tests.runtime.engagement.test_trace_replay_wiring import _primed_adapter  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _run_fire_window  # noqa: E402


_RUN_ID = "run:maintained_packet_ancestry"
_EPISODE_ID = "episode:maintained_packet_ancestry"
# The real deterministic seed the scenario is set up with (setup.seeds = [123]).
_SEED = 123
_WINDOW_EVIDENCE_MISMATCH = (
    "maintained_replay_envelope_window_evidence_does_not_match_minted_window"
)

_HAS_SLICE6A_BINDING = hasattr(ef_py.RuntimeFacade, "build_maintained_packet_ancestry")

# Loud skip, not silent absence: landing compiles the slice-6A surface and must
# re-run this file with zero skips.
_requires_binding = pytest.mark.skipif(
    not _HAS_SLICE6A_BINDING,
    reason=(
        "requires the T10 slice-6A RuntimeFacade.build_maintained_packet_ancestry "
        "binding: the local ef_py build predates this slice; landing must "
        "compile-verify and re-run with zero skips"
    ),
)


# --- Real-run fixtures ------------------------------------------------------


@pytest.fixture(scope="module")
def real_run() -> tuple[RuntimeFacadeAdapter, int, float]:
    """One opted-in adapter primed by really running the fire scenario."""
    return _primed_adapter(use_facade_evidence_producers=True)


def _real_window(real_run: tuple[RuntimeFacadeAdapter, int, float], tag: str) -> object:
    """Run one genuine maintained window and return its real evidence slice."""
    adapter, shooter_id, source_time_s = real_run
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, tag)
    assert evidence.window_result is not None
    assert evidence.engagement_packet is not None
    assert evidence.diagnostics_traces, "a real maintained window exports diagnostics traces"
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
    return adapter.build_maintained_packet_ancestry(**params)  # type: ignore[arg-type]


def _anchor(evidence: object) -> int:
    trace_ids = [int(value) for value in evidence.engagement_packet.trace_ids]
    assert trace_ids, "the opt-in path stamps a real minted trace id"
    return trace_ids[-1]


# --- The core evidence: an end-to-end ancestry chain over real windows ------


@_requires_binding
def test_real_run_root_ancestry_is_admitted_and_names_a_validated_envelope(real_run) -> None:
    """The slice's thesis at the chain root, proven on real evidence.

    A real window's real products yield an admitted root ancestry (no parent),
    whose replay_envelope_ref is exactly the same window's admitted maintained
    replay envelope -- and that envelope passes the independent WP15 validator.
    """
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "ancestry:root")
    result = _build(real_run, evidence)

    assert result.admitted, (result.rejection_reason, list(result.errors))
    assert result.rejection_reason == ""
    assert list(result.errors) == []

    anchor = _anchor(evidence)
    ancestry = result.ancestry
    assert ancestry.packet_ancestry_id == f"ancestry:maintained:{_RUN_ID}:trace:{anchor}"
    assert ancestry.run_id == _RUN_ID
    assert ancestry.episode_id == _EPISODE_ID
    assert int(ancestry.anchor_trace_id) == anchor
    # Root semantics: no parent, no parent event-order ref.
    assert int(ancestry.parent_trace_id) == 0
    assert ancestry.parent_event_order_ref == ""

    # Replay validation: the ref names the SAME window's admitted envelope.
    envelope_result = adapter.build_maintained_replay_envelope(
        run_id=_RUN_ID,
        episode_id=_EPISODE_ID,
        deterministic_seed=_SEED,
        window_evidence=evidence,
    )
    assert envelope_result.admitted, envelope_result.rejection_reason
    assert ancestry.replay_envelope_ref == envelope_result.envelope.replay_envelope_id
    assert ef_py.validate_replay_envelope(envelope_result.envelope).valid is True

    # Typed lineage refs (VA-5 vocabulary): replay envelope + anchor trace.
    lineage = [
        (ref.ref_id, ref.evidence_kind, ref.provenance_label)
        for ref in ancestry.lineage_refs
    ]
    assert lineage == [
        (ancestry.replay_envelope_ref, "replay_envelope", "replay"),
        (f"event:trace:{anchor}", "anchor_trace", "anchor"),
    ]

    # Root ancestral traces: copies of the window's real exported traces, every
    # parent still the pre-slice default 0.
    real_trace_ids = [int(trace.trace_id) for trace in evidence.diagnostics_traces]
    assert [int(trace.trace_id) for trace in ancestry.ancestral_traces] == real_trace_ids
    assert all(int(trace.parent_trace_id) == 0 for trace in ancestry.ancestral_traces)

    # Evidence refs: producer label first, then the deterministic key refs. The
    # linked count is read back out of the real window products (traces whose
    # trace_id is one of the packet's run-minted tags), not written as a literal.
    tag_set = {int(value) for value in evidence.engagement_packet.trace_ids}
    expected_linked = sum(
        1 for trace in evidence.diagnostics_traces if int(trace.trace_id) in tag_set
    )
    assert expected_linked >= 1
    assert list(result.evidence_refs) == [
        "RuntimeFacade.build_maintained_packet_ancestry",
        f"packet_ancestry_id={ancestry.packet_ancestry_id}",
        f"replay_envelope_ref={ancestry.replay_envelope_ref}",
        f"anchor_trace_id={anchor}",
        f"linked_trace_count={expected_linked}",
    ]


@_requires_binding
def test_real_run_end_to_end_ancestry_chain_across_windows(real_run) -> None:
    """Successive real windows chain through their genuinely minted anchors.

    Each link's parent is the PREVIOUS window's run-minted VA-8 anchor (the
    caller passes the previous result's anchor_trace_id, keeping the chain
    stateless and explicit), and every linked ancestral trace copy carries that
    parent -- the census slice-6 ``parent_trace_id`` gap, populated end-to-end
    on real evidence.
    """
    parent = 0
    anchors: list[int] = []
    ancestry_ids: list[str] = []
    for k in range(3):
        evidence = _real_window(real_run, f"ancestry:chain:{k}")
        result = _build(real_run, evidence, parent_trace_id=parent)
        assert result.admitted, (k, result.rejection_reason)
        ancestry = result.ancestry

        anchor = _anchor(evidence)
        assert int(ancestry.anchor_trace_id) == anchor
        assert int(ancestry.parent_trace_id) == parent
        if parent != 0:
            assert ancestry.parent_event_order_ref == f"event:trace:{parent}"
            # Every run-minted trace copy is linked to the parent anchor.
            tagged = [
                trace
                for trace in ancestry.ancestral_traces
                if int(trace.trace_id) in {int(v) for v in evidence.engagement_packet.trace_ids}
            ]
            assert tagged, "the opt-in window exports at least one tagged trace"
            assert all(int(trace.parent_trace_id) == parent for trace in tagged)
            # The parent edge appears in the typed lineage.
            assert (
                f"event:trace:{parent}",
                "parent_trace",
                "parent",
            ) in [
                (ref.ref_id, ref.evidence_kind, ref.provenance_label)
                for ref in ancestry.lineage_refs
            ]
        anchors.append(anchor)
        ancestry_ids.append(ancestry.packet_ancestry_id)
        parent = anchor

    # Real minted ids advance strictly, and each ancestry id embeds its own.
    assert anchors == sorted(anchors)
    assert len(set(anchors)) == 3
    assert len(set(ancestry_ids)) == 3
    for ancestry_id, anchor in zip(ancestry_ids, anchors):
        assert ancestry_id.endswith(f":trace:{anchor}")


@_requires_binding
def test_ancestry_population_returns_copies_and_mints_nothing(real_run) -> None:
    """Never mutate the default path in place; the producer is read-only.

    Building a parent-linked ancestry leaves the stored window product's traces
    at ``parent_trace_id = 0`` (the serialized default), consumes no allocator
    identity, and is idempotent.
    """
    adapter, _shooter_id, _source_time_s = real_run
    parent_evidence = _real_window(real_run, "copies:parent")
    evidence = _real_window(real_run, "copies:child")
    parent = _anchor(parent_evidence)
    trace_cursor = int(adapter.facade.peek_next_trace_id())
    snapshot_cursor = int(adapter.facade.peek_next_run_snapshot_version())

    first = _build(real_run, evidence, parent_trace_id=parent)
    second = _build(real_run, evidence, parent_trace_id=parent)

    assert first.admitted and second.admitted
    # The ancestral copies are linked...
    assert any(int(trace.parent_trace_id) == parent for trace in first.ancestry.ancestral_traces)
    # ...but the window products the run stored are byte-untouched.
    assert all(
        int(trace.parent_trace_id) == 0
        for trace in evidence.window_result.diagnostics_traces
    )
    assert all(int(trace.parent_trace_id) == 0 for trace in evidence.diagnostics_traces)
    # Idempotent and mint-free.
    assert first.ancestry.packet_ancestry_id == second.ancestry.packet_ancestry_id
    assert list(first.evidence_refs) == list(second.evidence_refs)
    assert int(adapter.facade.peek_next_trace_id()) == trace_cursor
    assert int(adapter.facade.peek_next_run_snapshot_version()) == snapshot_cursor


# --- Fail-closed gates: foreign/synthetic ancestry actually rejects ---------


@_requires_binding
def test_gate_parent_trace_id_not_minted_by_this_run(real_run) -> None:
    """A parent id this run's allocator never handed out is rejected.

    This is the decisive foreign-parent gate: an id exactly at the cursor was
    never minted here, so synthetic ancestry cannot be injected -- and the
    rejection leaks no partially assembled lineage.
    """
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "gate:parent_foreign")
    unminted = int(adapter.facade.peek_next_trace_id())

    result = _build(real_run, evidence, parent_trace_id=unminted)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_packet_ancestry_parent_trace_id_not_minted_by_this_run"
    )
    assert result.ancestry.packet_ancestry_id == ""
    assert list(result.ancestry.ancestral_traces) == []
    assert list(result.ancestry.lineage_refs) == []
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_allocated_but_unrecorded_parent_trace_id_is_rejected(real_run) -> None:
    """Allocation alone is not ancestry evidence; a prior window must record the anchor."""
    adapter, _shooter_id, _source_time_s = real_run
    allocated_without_window = int(adapter.facade.allocate_trace_id())
    evidence = _real_window(real_run, "gate:parent_allocated_without_window")
    assert allocated_without_window < _anchor(evidence)

    result = _build(real_run, evidence, parent_trace_id=allocated_without_window)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_packet_ancestry_parent_trace_id_not_minted_by_this_run"
    )
    assert result.ancestry.packet_ancestry_id == ""
    assert list(result.ancestry.ancestral_traces) == []
    assert list(result.ancestry.lineage_refs) == []
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_parent_must_strictly_precede_the_window(real_run) -> None:
    """Ancestry points backwards: a self-parent (or forward parent) is rejected."""
    evidence = _real_window(real_run, "gate:parent_self")
    result = _build(real_run, evidence, parent_trace_id=_anchor(evidence))
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_packet_ancestry_parent_trace_id_not_before_window_traces"
    )


@_requires_binding
def test_gate_foreign_facade_window_evidence_fails_closed(real_run) -> None:
    """Evidence minted by a DIFFERENT facade's allocator is rejected.

    A second opted-in run produces a real window carrying a different opaque
    facade identity; feeding it through THIS run's seam is rejected even when
    the two allocators overlap numerically.
    """
    adapter, _shooter_id, _source_time_s = real_run
    own_cursor = int(adapter.facade.peek_next_trace_id())
    if own_cursor == 1:
        assert int(adapter.facade.allocate_trace_id()) == 1
        own_cursor = int(adapter.facade.peek_next_trace_id())
    assert own_cursor > 1

    foreign_adapter, foreign_shooter, foreign_time = _primed_adapter(
        use_facade_evidence_producers=True
    )
    foreign_evidence = _run_fire_window(
        foreign_adapter, foreign_shooter, foreign_time, "foreign:overlap"
    )
    assert foreign_evidence is not None
    assert _anchor(foreign_evidence) == 1
    assert _anchor(foreign_evidence) < own_cursor

    result = _build(real_run, foreign_evidence)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_replay_envelope_window_identity_not_minted_by_this_facade"
    )


@_requires_binding
def test_gate_default_placeholder_evidence_is_inadmissible(real_run) -> None:
    """The slice-5 gates guard this producer too (rejections propagate verbatim).

    A real DEFAULT-path window (placeholder trace_ids = [1], allocator cursor
    still 1) reaches the C++ producer directly -- bypassing the adapter's
    opt-in guard -- and is still rejected by the reused VA-8 admission gate.
    """
    default_adapter, shooter_id, source_time_s = _primed_adapter(
        use_facade_evidence_producers=False
    )
    evidence = _run_fire_window(default_adapter, shooter_id, source_time_s, "gate:default")
    assert [int(value) for value in evidence.engagement_packet.trace_ids] == [1]
    assert int(default_adapter.facade.peek_next_trace_id()) == 1

    result = default_adapter.facade.build_maintained_packet_ancestry(
        evidence.window_result, _RUN_ID, _EPISODE_ID, _SEED
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_replay_envelope_trace_ids_not_minted_by_this_run"
    )


@_requires_binding
def test_mutated_window_diagnostics_traces_are_rejected(real_run) -> None:
    evidence = _real_window(real_run, "gate:traces_missing")
    evidence.window_result.diagnostics_traces = []
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


@_requires_binding
def test_mutated_window_trace_tags_are_rejected(real_run) -> None:
    """A copied genuine token cannot authenticate retagged diagnostics traces."""
    evidence = _real_window(real_run, "gate:untagged")
    retagged = list(evidence.window_result.diagnostics_traces)
    assert retagged
    for trace in retagged:
        trace.trace_id = int(trace.trace_id) + 1_000_000
    evidence.window_result.diagnostics_traces = retagged
    result = _build(real_run, evidence)
    assert result.admitted is False
    assert result.rejection_reason == _WINDOW_EVIDENCE_MISMATCH


# --- The adapter seam's opt-in contract (runs on any build) -----------------


def test_seam_requires_the_optin_evidence_producers() -> None:
    """``use_facade_evidence_producers=False`` raises the named RuntimeError.

    Asserted without priming a run: the guard precedes any window lookup and
    any binding probe, so this pins the I59 discipline on every build.
    """
    adapter = RuntimeFacadeAdapter(1)
    assert adapter.use_facade_evidence_producers is False

    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True") as exc:
        adapter.build_maintained_packet_ancestry(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )
    message = str(exc.value)
    assert "packet ancestry" in message
    assert "placeholder" in message


@pytest.mark.skipif(
    _HAS_SLICE6A_BINDING,
    reason="binding present: the missing-binding seam error is unreachable on this build",
)
def test_seam_names_the_missing_slice6a_binding() -> None:
    """On a pre-slice-6A build the seam fails fast with the named binding error,
    not a bare AttributeError leaking from the facade surface."""
    adapter = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
    with pytest.raises(
        RuntimeError,
        match=r"requires the T10 slice-6A RuntimeFacade\.build_maintained_packet_ancestry",
    ):
        adapter.build_maintained_packet_ancestry(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )


@_requires_binding
def test_seam_requires_a_completed_window(real_run) -> None:
    """The missing-window error path mirrors the slice-5 seam contract."""
    fresh = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
    assert fresh.last_window_evidence is None
    with pytest.raises(RuntimeError, match=r"completed maintained window"):
        fresh.build_maintained_packet_ancestry(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )


@_requires_binding
def test_seam_defaults_to_the_last_real_window(real_run) -> None:
    """Omitting ``window_evidence`` uses the run's own most recent real window."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "implicit")
    assert adapter.last_window_evidence is evidence

    implicit = adapter.build_maintained_packet_ancestry(
        run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
    )
    explicit = _build(real_run, evidence)
    assert implicit.admitted and explicit.admitted
    assert implicit.ancestry.packet_ancestry_id == explicit.ancestry.packet_ancestry_id


# --- The default (non-opt-in) path is unchanged (runs on any build) ---------


def test_default_maintained_path_still_carries_the_placeholder_evidence() -> None:
    """The additive red line: the non-opt-in run is untouched by this slice.

    A default adapter runs the same real scenario and still produces the
    pre-slice placeholder evidence -- trace_ids [1], both run-global cursors
    never advanced, and every exported trace's ``parent_trace_id`` at the
    serialized default 0 -- so nothing slice 6A added can have perturbed a
    default-path serialized value. The seam stays shut on this path.
    """
    adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, "slice6a:default")

    assert [int(value) for value in evidence.engagement_packet.trace_ids] == [1]
    assert int(adapter.facade.peek_next_trace_id()) == 1
    assert int(adapter.facade.peek_next_run_snapshot_version()) == 1
    # The census slice-6 gap value, still byte-identical on the default path.
    assert all(int(trace.parent_trace_id) == 0 for trace in evidence.diagnostics_traces)
    assert all(
        int(trace.parent_trace_id) == 0
        for trace in evidence.engagement_packet.diagnostics_traces
    )

    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True"):
        adapter.build_maintained_packet_ancestry(
            run_id=_RUN_ID, episode_id=_EPISODE_ID, deterministic_seed=_SEED
        )
