"""Real-run end-to-end proof for the T10 slice-7 maintained worldline comparison.

Slice 7 of the T10 evidence-spine census order (see
``docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md``
section 3 step 7) adds ``RuntimeFacade::build_maintained_worldline_comparison``
(this iteration): a read-only producer that joins TWO maintained windows of one
facade run -- a baseline worldline and a candidate (counterfactual) worldline --
into an evidence-level comparison, consuming the slice-5 (I69) maintained
replay envelopes and the slice-6A (I79) maintained packet ancestry of both
sides, and exposed opt-in through the maintained adapter seam
``RuntimeFacadeAdapter.build_maintained_worldline_comparison``.

Every admitted comparison asserted here comes from **actual scenarios** (the
same seed-123 two-aircraft fire engagement the I59 slice-4 gates run, plus a
two-world same-scenario variant seeded 123 vs 456 for the different-seed
worldline pair), driven through **actual maintained windows**
(``RuntimeFacadeAdapter.run_maintained_window`` over the real
``RuntimeFacade::run_window``), carrying **real exported packets**.

What is pinned:

* real-run comparison evidence: an admitted comparison over two real windows
  whose envelope refs are exactly the same windows' admitted maintained replay
  envelopes (each independently passing the fail-closed WP15
  ``validate_replay_envelope``, which requires the deterministic seed and the
  deterministic event-order sort key -- the deterministic replay refs), and
  whose ancestry refs are exactly the same windows' admitted slice-6A
  ancestries;
* the same-seed / different-seed worldline pair: two worlds of one run set up
  with equal seeds compare with ``deterministic_seed_matched=True``, a
  123-vs-456 pair records the mismatch -- both admitted, both replayable;
* NO TRUTH PROMOTION (the slice red line): the comparison DTO carries evidence
  ids only -- no kinematic delta or truth-state field exists on the bound
  surface (unlike the raw ``RuntimeWorldlineComparison``'s dx/dy/dz family),
  ``truth_claim``/``promoted_to_support`` are structurally ``False``, and
  ``claim_scope`` is the contract-owned ``"comparative"``;
* default-path byte parity: the producer is read-only (both run-global cursors
  untouched, stored window products byte-untouched, idempotent), zero-wired
  (nothing on the default path calls it), and the default (non-opt-in)
  maintained path still carries the placeholder evidence unchanged;
* fail-closed gates by perturbation: foreign-facade candidate evidence, an
  unminted ancestry parent, a self-comparison (shared anchor), and the default
  placeholder evidence each reject with a named reason -- the side-naming
  comparison wrapper carrying the underlying slice-5/6A reason in ``errors`` --
  and leak no partially assembled evidence join;
* the seam's opt-in contract: ``use_facade_evidence_producers=False`` raises
  the named ``RuntimeError`` before any window lookup (I59 discipline).

Build-surface note (this iteration): C++ compilation happens at landing, so the
slice-7-binding-dependent tests below skip -- loudly, via ``_requires_binding``
-- when the local ``ef_py`` build predates this slice. Landing MUST
compile-verify and re-run this file expecting zero ``_requires_binding`` skips
(the only remaining skip is ``test_seam_names_the_missing_slice7_binding``,
which is reachable only on a pre-slice-7 build by construction); the two-world
envelope prerequisite (slice-5 binding), seam-guard, and default-parity tests
run on the current wave-head build already.

Smoke registration: deliberately not added to ``tests/smoke/ci_smoke_suite.json``,
matching the slice-4/5/6A precedent (``test_trace_replay_wiring.py`` /
``test_maintained_replay_envelope.py`` / ``test_maintained_packet_ancestry.py``
are likewise excluded): these are real engine runs priming 80-step scenarios
per adapter (several adapters here, including a two-world one), and the
default-path serialized surface they guard is already smoke-pinned by
``test_trace_replay_gates.py``.
"""

from __future__ import annotations

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter  # noqa: E402

# The slice-4 (I59) gates own the real seed-123 fire-engagement scenario driven
# entirely through the public adapter API; slices 5 (I69) and 6A (I79) reuse it
# for the same reason this file does: one shared "real run" definition that
# cannot fork.
from tests.runtime.engagement.test_trace_replay_wiring import _DB_PATH  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _make_pilot_fire_action  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _make_spawn_request  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _primed_adapter  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _run_fire_window  # noqa: E402
from tests.runtime.engagement.test_trace_replay_wiring import _world_ref  # noqa: E402


_RUN_ID = "run:maintained_worldline_comparison"
_EPISODE_ID = "episode:maintained_worldline_comparison"
# The real deterministic seed the single-world scenario is set up with
# (setup.seeds = [123]) and the two-world pair's second seed.
_SEED = 123
_CANDIDATE_SEED = 456
_WINDOW_EVIDENCE_MISMATCH = (
    "maintained_replay_envelope_window_evidence_does_not_match_minted_window"
)

_HAS_SLICE5_BINDING = hasattr(ef_py.RuntimeFacade, "build_maintained_replay_envelope")
_HAS_SLICE7_BINDING = hasattr(ef_py.RuntimeFacade, "build_maintained_worldline_comparison")

# Loud skip, not silent absence: landing compiles the slice-7 surface and must
# re-run this file with zero skips.
_requires_binding = pytest.mark.skipif(
    not _HAS_SLICE7_BINDING,
    reason=(
        "requires the T10 slice-7 RuntimeFacade.build_maintained_worldline_comparison "
        "binding: the local ef_py build predates this slice; landing must "
        "compile-verify and re-run with zero skips"
    ),
)

_requires_slice5_binding = pytest.mark.skipif(
    not _HAS_SLICE5_BINDING,
    reason="requires the T10 slice-5 RuntimeFacade.build_maintained_replay_envelope binding",
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


def _anchor(evidence: object) -> int:
    trace_ids = [int(value) for value in evidence.engagement_packet.trace_ids]
    assert trace_ids, "the opt-in path stamps a real minted trace id"
    return trace_ids[-1]


def _compare(
    adapter: RuntimeFacadeAdapter,
    baseline_evidence: object,
    candidate_evidence: object,
    **kwargs: object,
) -> object:
    params: dict[str, object] = {
        "run_id": _RUN_ID,
        "episode_id": _EPISODE_ID,
        "baseline_deterministic_seed": _SEED,
        "candidate_deterministic_seed": _SEED,
        "baseline_window_evidence": baseline_evidence,
        "candidate_window_evidence": candidate_evidence,
    }
    params.update(kwargs)
    return adapter.build_maintained_worldline_comparison(**params)  # type: ignore[arg-type]


# --- Two-world real-run fixture (same scenario, per-world seeds) ------------


def _apply_two_world_fire_scenario(
    adapter: RuntimeFacadeAdapter, seeds: tuple[int, int]
) -> tuple[dict[int, int], dict[int, float]]:
    """Really set up and prime the fire scenario in BOTH worlds of one facade.

    The same two-aircraft engagement the I59 helper builds, duplicated per
    world with per-world seeds -- two parallel worldlines of ONE run (one
    facade == one run == one VA-8 allocator), which is exactly what makes a
    same-seed/different-seed pair comparable by THIS facade's producer.
    """
    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [int(seeds[0]), int(seeds[1])]
    terrain_assignments = []
    wind_assignments = []
    spawn_requests = []
    for world_index in (0, 1):
        terrain = ef_py.WorldTerrainAssignment()
        terrain.world_index = world_index
        terrain.terrain_type = "flat"
        terrain_assignments.append(terrain)
        wind = ef_py.WorldWindAssignment()
        wind.world_index = world_index
        wind_assignments.append(wind)
        blue = _make_spawn_request(
            side=ef_py.Side.Blue,
            type_name="F-16C_Block50",
            entity_name=f"Blue{world_index}",
            y=0.0,
            heading=0.0,
            vy=250.0,
            is_agent=True,
        )
        blue.world_index = world_index
        red = _make_spawn_request(
            side=ef_py.Side.Red,
            type_name="Aircraft",
            entity_name=f"Red{world_index}",
            y=30000.0,
            heading=180.0,
            vy=-250.0,
            is_agent=False,
        )
        red.world_index = world_index
        spawn_requests.extend([blue, red])
    setup.terrain_assignments = terrain_assignments
    setup.wind_assignments = wind_assignments
    setup.spawn_requests = spawn_requests
    setup.time_steps = [0.05, 0.05]
    setup_result = adapter.apply_world_setup(setup)
    entity_ids = [int(value) for value in setup_result.entity_ids]
    assert len(entity_ids) == 4, entity_ids
    shooters = {0: entity_ids[0], 1: entity_ids[2]}
    targets = {0: entity_ids[1], 1: entity_ids[3]}

    pending = {0, 1}
    source_times: dict[int, float] = {}
    for _ in range(160):
        adapter.step_batch()
        for world_index in sorted(pending):
            obs = adapter.get_agent_observations_batch(
                [_world_ref(world_index, shooters[world_index])]
            )[0]
            if any(
                int(track.id) == targets[world_index]
                for track in getattr(obs, "contacts", [])
            ):
                source_times[world_index] = float(getattr(obs, "sim_time", 0.0) or 0.0)
                pending.discard(world_index)
        if not pending:
            break
    else:
        raise AssertionError(
            "expected both worlds' shooters to expose a target contact"
        )
    return shooters, source_times


def _run_fire_window_in_world(
    adapter: RuntimeFacadeAdapter,
    world_index: int,
    shooter_id: int,
    source_time_s: float,
    tag: str,
) -> object:
    evidence = adapter.run_maintained_window(
        world_index=int(world_index),
        entity_id=int(shooter_id),
        pilot_action=_make_pilot_fire_action(),
        source_time_s=source_time_s,
        window_id=f"worldline_comparison:{tag}",
        source_layer="training_policy",
        information_state_label="facade_observation_packet",
        action_family="direct_control",
        include_engagement=True,
        include_diagnostics=True,
    )
    assert evidence is not None, "run_maintained_window requires the RuntimeFacade window API"
    assert evidence.diagnostics_traces, "a real maintained window exports diagnostics traces"
    return evidence


@pytest.fixture(scope="module")
def two_world_run() -> tuple[RuntimeFacadeAdapter, dict[int, int], dict[int, float]]:
    """One opted-in TWO-world adapter, worlds seeded 123 vs 456, both primed."""
    adapter = RuntimeFacadeAdapter(2, use_facade_evidence_producers=True)
    if not adapter.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    shooters, source_times = _apply_two_world_fire_scenario(adapter, (_SEED, _CANDIDATE_SEED))
    return adapter, shooters, source_times


# --- The core evidence: real-run comparisons over real windows --------------


@_requires_binding
def test_real_run_same_seed_comparison_is_admitted_with_validated_replay_refs(real_run) -> None:
    """The slice's thesis on real evidence: two real windows of one run join
    into an admitted comparison whose replay refs are exactly the same windows'
    admitted maintained envelopes, each passing the independent WP15 validator.
    """
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "same_seed:baseline")
    candidate = _real_window(real_run, "same_seed:candidate")
    baseline_anchor = _anchor(baseline)
    candidate_anchor = _anchor(candidate)

    result = _compare(
        adapter,
        baseline,
        candidate,
        candidate_parent_trace_id=baseline_anchor,
    )
    assert result.admitted, (result.rejection_reason, list(result.errors))
    assert result.rejection_reason == ""
    assert list(result.errors) == []

    comparison = result.comparison
    assert comparison.comparison_id == (
        f"comparison:maintained:{_RUN_ID}:trace:{baseline_anchor}:vs:{candidate_anchor}"
    )
    assert comparison.run_id == _RUN_ID
    assert comparison.episode_id == _EPISODE_ID
    assert comparison.baseline_worldline_id == (
        f"worldline:maintained:{_RUN_ID}:trace:{baseline_anchor}"
    )
    assert comparison.candidate_worldline_id == (
        f"worldline:maintained:{_RUN_ID}:trace:{candidate_anchor}"
    )
    assert int(comparison.baseline_anchor_trace_id) == baseline_anchor
    assert int(comparison.candidate_anchor_trace_id) == candidate_anchor

    # Replay validation, per side: the refs name the SAME windows' admitted
    # slice-5 envelopes, and each envelope passes the independent fail-closed
    # WP15 validator (which requires the deterministic seed and the
    # deterministic event-order sort key -- the deterministic replay refs).
    for window_evidence, envelope_ref, event_order_ref, snapshot_version_ref in (
        (
            baseline,
            comparison.baseline_replay_envelope_ref,
            comparison.baseline_event_order_ref,
            comparison.baseline_snapshot_version_ref,
        ),
        (
            candidate,
            comparison.candidate_replay_envelope_ref,
            comparison.candidate_event_order_ref,
            comparison.candidate_snapshot_version_ref,
        ),
    ):
        envelope_result = adapter.build_maintained_replay_envelope(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            deterministic_seed=_SEED,
            window_evidence=window_evidence,
        )
        assert envelope_result.admitted, envelope_result.rejection_reason
        assert envelope_ref == envelope_result.envelope.replay_envelope_id
        assert event_order_ref == envelope_result.envelope.event_order_ref.event_id
        assert (
            snapshot_version_ref
            == envelope_result.envelope.snapshot_ref.snapshot_version_ref
        )
        assert ef_py.validate_replay_envelope(envelope_result.envelope).valid is True

    # Ancestry consumption (I79): the ancestry refs name the SAME windows'
    # admitted slice-6A ancestries under the same parents.
    baseline_ancestry = adapter.build_maintained_packet_ancestry(
        run_id=_RUN_ID,
        episode_id=_EPISODE_ID,
        deterministic_seed=_SEED,
        window_evidence=baseline,
    )
    candidate_ancestry = adapter.build_maintained_packet_ancestry(
        run_id=_RUN_ID,
        episode_id=_EPISODE_ID,
        deterministic_seed=_SEED,
        window_evidence=candidate,
        parent_trace_id=baseline_anchor,
    )
    assert baseline_ancestry.admitted and candidate_ancestry.admitted
    assert (
        comparison.baseline_packet_ancestry_ref
        == baseline_ancestry.ancestry.packet_ancestry_id
    )
    assert (
        comparison.candidate_packet_ancestry_ref
        == candidate_ancestry.ancestry.packet_ancestry_id
    )

    # Same-seed pair: seeds echoed, match recorded; no truth promotion.
    assert int(comparison.baseline_deterministic_seed) == _SEED
    assert int(comparison.candidate_deterministic_seed) == _SEED
    assert comparison.deterministic_seed_matched is True
    assert comparison.claim_scope == "comparative"
    assert comparison.truth_claim is False
    assert comparison.promoted_to_support is False

    # Typed lineage refs (VA-5 vocabulary): envelope + ancestry + anchor per
    # side, baseline first. Deterministic order.
    lineage = [
        (ref.ref_id, ref.evidence_kind, ref.provenance_label)
        for ref in comparison.lineage_refs
    ]
    assert lineage == [
        (comparison.baseline_replay_envelope_ref, "replay_envelope", "baseline"),
        (comparison.baseline_packet_ancestry_ref, "packet_ancestry", "baseline"),
        (f"event:trace:{baseline_anchor}", "anchor_trace", "baseline"),
        (comparison.candidate_replay_envelope_ref, "replay_envelope", "candidate"),
        (comparison.candidate_packet_ancestry_ref, "packet_ancestry", "candidate"),
        (f"event:trace:{candidate_anchor}", "anchor_trace", "candidate"),
    ]

    # Evidence refs: producer label first, then the deterministic key refs.
    assert list(result.evidence_refs) == [
        "RuntimeFacade.build_maintained_worldline_comparison",
        f"comparison_id={comparison.comparison_id}",
        f"baseline_replay_envelope_ref={comparison.baseline_replay_envelope_ref}",
        f"candidate_replay_envelope_ref={comparison.candidate_replay_envelope_ref}",
        f"baseline_packet_ancestry_ref={comparison.baseline_packet_ancestry_ref}",
        f"candidate_packet_ancestry_ref={comparison.candidate_packet_ancestry_ref}",
        "deterministic_seed_matched=true",
    ]


@_requires_binding
def test_real_run_different_seed_worldlines_record_the_seed_mismatch(two_world_run) -> None:
    """A 123-vs-456 worldline pair -- two worlds of ONE run, really primed and
    really windowed -- compares admitted with the seed mismatch recorded, so a
    consumer can tell a same-seed replay pair from a divergent-seed pair
    without any truth-state copy.
    """
    adapter, shooters, source_times = two_world_run
    baseline = _run_fire_window_in_world(
        adapter, 0, shooters[0], source_times[0], "diff_seed:baseline"
    )
    candidate = _run_fire_window_in_world(
        adapter, 1, shooters[1], source_times[1], "diff_seed:candidate"
    )
    baseline_anchor = _anchor(baseline)
    candidate_anchor = _anchor(candidate)
    assert baseline_anchor != candidate_anchor

    result = _compare(
        adapter,
        baseline,
        candidate,
        candidate_deterministic_seed=_CANDIDATE_SEED,
    )
    assert result.admitted, (result.rejection_reason, list(result.errors))

    comparison = result.comparison
    assert int(comparison.baseline_deterministic_seed) == _SEED
    assert int(comparison.candidate_deterministic_seed) == _CANDIDATE_SEED
    assert comparison.deterministic_seed_matched is False
    assert comparison.baseline_worldline_id != comparison.candidate_worldline_id
    assert (
        comparison.baseline_replay_envelope_ref
        != comparison.candidate_replay_envelope_ref
    )
    assert (
        comparison.baseline_packet_ancestry_ref
        != comparison.candidate_packet_ancestry_ref
    )
    assert result.evidence_refs[-1] == "deterministic_seed_matched=false"


@_requires_binding
def test_comparison_is_read_only_idempotent_and_mints_nothing(real_run) -> None:
    """The producer never mutates the run: cursors untouched, stored window
    products byte-untouched, repeated calls identical."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "readonly:baseline")
    candidate = _real_window(real_run, "readonly:candidate")
    trace_cursor = int(adapter.facade.peek_next_trace_id())
    snapshot_cursor = int(adapter.facade.peek_next_run_snapshot_version())

    first = _compare(adapter, baseline, candidate)
    second = _compare(adapter, baseline, candidate)

    assert first.admitted and second.admitted
    assert first.comparison.comparison_id == second.comparison.comparison_id
    assert list(first.evidence_refs) == list(second.evidence_refs)
    assert int(adapter.facade.peek_next_trace_id()) == trace_cursor
    assert int(adapter.facade.peek_next_run_snapshot_version()) == snapshot_cursor
    # The stored window products keep the serialized defaults (no in-place
    # parent grafting, no trace mutation).
    for evidence in (baseline, candidate):
        assert all(
            int(trace.parent_trace_id) == 0
            for trace in evidence.window_result.diagnostics_traces
        )


@_requires_binding
def test_no_truth_state_red_line_comparison_carries_evidence_ids_only(real_run) -> None:
    """NO TRUTH PROMOTION: the bound comparison surface has no truth-state or
    kinematic-delta field (unlike the raw RuntimeWorldlineComparison), only
    ids/refs, seeds, and the structurally false claim flags."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "redline:baseline")
    candidate = _real_window(real_run, "redline:candidate")
    result = _compare(adapter, baseline, candidate)
    assert result.admitted, result.rejection_reason
    comparison = result.comparison

    # The raw counterfactual comparison's truth-delta vocabulary must not
    # appear here, nor any bare kinematic field.
    for truth_shaped in (
        "dx", "dy", "dz", "dvx", "dvy", "dvz", "dheading",
        "x", "y", "z", "vx", "vy", "vz", "heading", "pitch", "roll",
    ):
        assert not hasattr(comparison, truth_shaped), truth_shaped

    # The full public surface is exactly the evidence-reference field set.
    public_fields = {
        name
        for name in dir(comparison)
        if not name.startswith("_") and not callable(getattr(comparison, name))
    }
    assert public_fields == {
        "comparison_id",
        "run_id",
        "episode_id",
        "baseline_worldline_id",
        "candidate_worldline_id",
        "baseline_anchor_trace_id",
        "candidate_anchor_trace_id",
        "baseline_replay_envelope_ref",
        "candidate_replay_envelope_ref",
        "baseline_packet_ancestry_ref",
        "candidate_packet_ancestry_ref",
        "baseline_event_order_ref",
        "candidate_event_order_ref",
        "baseline_snapshot_version_ref",
        "candidate_snapshot_version_ref",
        "baseline_deterministic_seed",
        "candidate_deterministic_seed",
        "deterministic_seed_matched",
        "claim_scope",
        "truth_claim",
        "promoted_to_support",
        "lineage_refs",
    }
    assert comparison.truth_claim is False
    assert comparison.promoted_to_support is False
    assert comparison.claim_scope == "comparative"


# --- Fail-closed gates: foreign/synthetic comparisons actually reject -------


@_requires_binding
def test_gate_windows_sharing_the_anchor_are_rejected(real_run) -> None:
    """A window joined against itself is not a worldline comparison, and the
    rejection leaks no partially assembled evidence join."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "gate:self")
    result = _compare(adapter, evidence, evidence)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_windows_share_the_anchor_trace"
    )
    assert result.comparison.comparison_id == ""
    assert result.comparison.baseline_worldline_id == ""
    assert list(result.comparison.lineage_refs) == []
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_foreign_facade_candidate_evidence_fails_closed(real_run) -> None:
    """Candidate evidence minted by a DIFFERENT facade's allocator is rejected
    through the opaque window/facade identity gate, wrapped in the side-naming
    candidate reason with the underlying reason in errors."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "gate:foreign_baseline")
    own_cursor = int(adapter.facade.peek_next_trace_id())

    foreign_adapter, foreign_shooter, foreign_time = _primed_adapter(
        use_facade_evidence_producers=True
    )
    # The foreign facade's first anchor deliberately overlaps a numeric id that
    # this facade has already minted; identity, not cursor range, must reject it.
    foreign_evidence = _run_fire_window(
        foreign_adapter, foreign_shooter, foreign_time, "foreign:overlap"
    )
    assert foreign_evidence is not None
    assert own_cursor > 1
    assert _anchor(foreign_evidence) == 1
    assert _anchor(foreign_evidence) < own_cursor

    result = _compare(adapter, baseline, foreign_evidence)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_candidate_envelope_rejected"
    )
    assert list(result.errors)[0] == (
        "maintained_replay_envelope_window_identity_not_minted_by_this_facade"
    )
    assert result.comparison.comparison_id == ""
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_mutated_candidate_evidence_reports_the_candidate_side(real_run) -> None:
    """A genuine token cannot authenticate candidate fields changed after run_window."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "gate:mutated_candidate_baseline")
    candidate = _real_window(real_run, "gate:mutated_candidate")
    candidate.window_result.context.source_time_s = (
        float(candidate.window_result.context.source_time_s) + 1.0
    )

    result = _compare(adapter, baseline, candidate)
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_candidate_envelope_rejected"
    )
    assert list(result.errors) == [_WINDOW_EVIDENCE_MISMATCH]
    assert result.comparison.comparison_id == ""
    assert list(result.comparison.lineage_refs) == []
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_hand_built_candidate_reports_the_candidate_side(real_run) -> None:
    """A caller-built candidate has no opaque token and fails on its own side."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "gate:synthetic_candidate_baseline")
    hand_built_candidate = ef_py.RuntimeWindowResult()

    result = adapter.facade.build_maintained_worldline_comparison(
        baseline.window_result,
        hand_built_candidate,
        _RUN_ID,
        _EPISODE_ID,
        _SEED,
        _SEED,
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_candidate_envelope_rejected"
    )
    assert list(result.errors) == [
        "maintained_replay_envelope_window_identity_missing"
    ]
    assert result.comparison.comparison_id == ""
    assert list(result.evidence_refs) == []


@_requires_binding
def test_gate_worldline_keeps_baseline_first_when_both_sides_are_invalid() -> None:
    """The candidate must not mask a baseline identity rejection."""
    local = ef_py.RuntimeFacade(0)
    foreign = ef_py.RuntimeFacade(0)
    foreign_baseline = foreign.run_window(ef_py.RuntimeWindowRequest())
    hand_built_candidate = ef_py.RuntimeWindowResult()

    result = local.build_maintained_worldline_comparison(
        foreign_baseline,
        hand_built_candidate,
        _RUN_ID,
        _EPISODE_ID,
        _SEED,
        _SEED,
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_baseline_envelope_rejected"
    )
    assert list(result.errors) == [
        "maintained_replay_envelope_window_identity_not_minted_by_this_facade"
    ]


@_requires_binding
def test_gate_unminted_baseline_parent_fails_closed(real_run) -> None:
    """An ancestry parent this run never minted rejects through the reused
    slice-6A parent gate, wrapped in the side-naming baseline reason."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "gate:parent_baseline")
    candidate = _real_window(real_run, "gate:parent_candidate")
    unminted = int(adapter.facade.peek_next_trace_id())

    result = _compare(
        adapter, baseline, candidate, baseline_parent_trace_id=unminted
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_baseline_ancestry_rejected"
    )
    assert list(result.errors)[0] == (
        "maintained_packet_ancestry_parent_trace_id_not_minted_by_this_run"
    )
    assert result.comparison.comparison_id == ""


@_requires_binding
def test_gate_default_placeholder_evidence_is_inadmissible() -> None:
    """The slice-5 gates guard this producer too: a real DEFAULT-path run's
    windows (placeholder trace_ids = [1], allocator cursor still 1) reach the
    C++ producer directly -- bypassing the adapter's opt-in guard -- and are
    rejected on the baseline side by the reused VA-8 admission gate."""
    default_adapter, shooter_id, source_time_s = _primed_adapter(
        use_facade_evidence_producers=False
    )
    baseline = _run_fire_window(default_adapter, shooter_id, source_time_s, "gate:default_a")
    candidate = _run_fire_window(default_adapter, shooter_id, source_time_s, "gate:default_b")
    assert [int(value) for value in baseline.engagement_packet.trace_ids] == [1]
    assert int(default_adapter.facade.peek_next_trace_id()) == 1

    result = default_adapter.facade.build_maintained_worldline_comparison(
        baseline.window_result,
        candidate.window_result,
        _RUN_ID,
        _EPISODE_ID,
        _SEED,
        _SEED,
    )
    assert result.admitted is False
    assert result.rejection_reason == (
        "maintained_worldline_comparison_baseline_envelope_rejected"
    )
    assert list(result.errors)[0] == (
        "maintained_replay_envelope_trace_ids_not_minted_by_this_run"
    )


# --- The adapter seam's opt-in contract (runs on any build) -----------------


def test_seam_requires_the_optin_evidence_producers() -> None:
    """``use_facade_evidence_producers=False`` raises the named RuntimeError.

    Asserted without priming a run: the guard precedes any window lookup and
    any binding probe, so this pins the I59 discipline on every build.
    """
    adapter = RuntimeFacadeAdapter(1)
    assert adapter.use_facade_evidence_producers is False

    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True") as exc:
        adapter.build_maintained_worldline_comparison(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            baseline_deterministic_seed=_SEED,
            candidate_deterministic_seed=_SEED,
            baseline_window_evidence=None,  # type: ignore[arg-type]
        )
    message = str(exc.value)
    assert "worldline comparison" in message
    assert "placeholder" in message


@pytest.mark.skipif(
    _HAS_SLICE7_BINDING,
    reason="binding present: the missing-binding seam error is unreachable on this build",
)
def test_seam_names_the_missing_slice7_binding() -> None:
    """On a pre-slice-7 build the seam fails fast with the named binding error,
    not a bare AttributeError leaking from the facade surface."""
    adapter = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
    with pytest.raises(
        RuntimeError,
        match=r"requires the T10 slice-7 RuntimeFacade\.build_maintained_worldline_comparison",
    ):
        adapter.build_maintained_worldline_comparison(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            baseline_deterministic_seed=_SEED,
            candidate_deterministic_seed=_SEED,
            baseline_window_evidence=None,  # type: ignore[arg-type]
        )


@_requires_binding
def test_seam_requires_completed_windows(real_run) -> None:
    """Both window slots demand completed maintained windows: the baseline is
    always explicit, the candidate falls back to the last real window and
    fails fast when there is none."""
    adapter, _shooter_id, _source_time_s = real_run
    evidence = _real_window(real_run, "seam:windows")

    with pytest.raises(RuntimeError, match=r"completed maintained baseline window"):
        adapter.build_maintained_worldline_comparison(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            baseline_deterministic_seed=_SEED,
            candidate_deterministic_seed=_SEED,
            baseline_window_evidence=None,  # type: ignore[arg-type]
        )

    fresh = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
    assert fresh.last_window_evidence is None
    with pytest.raises(RuntimeError, match=r"completed maintained candidate window"):
        fresh.build_maintained_worldline_comparison(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            baseline_deterministic_seed=_SEED,
            candidate_deterministic_seed=_SEED,
            baseline_window_evidence=evidence,
        )


@_requires_binding
def test_seam_defaults_candidate_to_the_last_real_window(real_run) -> None:
    """Omitting ``candidate_window_evidence`` uses the run's own most recent
    real window as the candidate worldline."""
    adapter, _shooter_id, _source_time_s = real_run
    baseline = _real_window(real_run, "seam:implicit_baseline")
    candidate = _real_window(real_run, "seam:implicit_candidate")
    assert adapter.last_window_evidence is candidate

    implicit = adapter.build_maintained_worldline_comparison(
        run_id=_RUN_ID,
        episode_id=_EPISODE_ID,
        baseline_deterministic_seed=_SEED,
        candidate_deterministic_seed=_SEED,
        baseline_window_evidence=baseline,
    )
    explicit = _compare(adapter, baseline, candidate)
    assert implicit.admitted and explicit.admitted
    assert implicit.comparison.comparison_id == explicit.comparison.comparison_id


# --- Local prerequisite + the default path is unchanged (any build) ---------


@_requires_slice5_binding
def test_two_world_optin_windows_yield_independently_admitted_envelopes(two_world_run) -> None:
    """The two-world worldline pair is real evidence on the CURRENT build: both
    worlds' windows carry distinct facade-minted anchors and each admits its
    own slice-5 maintained replay envelope. (This pins the comparison's inputs
    without the slice-7 binding, so the machinery is verified before landing
    compiles the producer.)"""
    adapter, shooters, source_times = two_world_run
    baseline = _run_fire_window_in_world(
        adapter, 0, shooters[0], source_times[0], "prereq:baseline"
    )
    candidate = _run_fire_window_in_world(
        adapter, 1, shooters[1], source_times[1], "prereq:candidate"
    )
    baseline_anchor = _anchor(baseline)
    candidate_anchor = _anchor(candidate)
    assert baseline_anchor != candidate_anchor
    assert candidate_anchor > baseline_anchor  # one allocator, monotone across worlds

    envelope_ids = []
    for window_evidence in (baseline, candidate):
        envelope_result = adapter.build_maintained_replay_envelope(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            deterministic_seed=_SEED,
            window_evidence=window_evidence,
        )
        assert envelope_result.admitted, envelope_result.rejection_reason
        assert ef_py.validate_replay_envelope(envelope_result.envelope).valid is True
        envelope_ids.append(envelope_result.envelope.replay_envelope_id)
    assert len(set(envelope_ids)) == 2


def test_default_maintained_path_still_carries_the_placeholder_evidence() -> None:
    """The additive red line: the non-opt-in run is untouched by this slice.

    A default adapter runs the same real scenario and still produces the
    pre-slice placeholder evidence -- trace_ids [1], both run-global cursors
    never advanced, every exported trace parent at the serialized default 0 --
    so nothing slice 7 added can have perturbed a default-path serialized
    value. The seam stays shut on this path.
    """
    adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, "slice7:default")

    assert [int(value) for value in evidence.engagement_packet.trace_ids] == [1]
    assert int(adapter.facade.peek_next_trace_id()) == 1
    assert int(adapter.facade.peek_next_run_snapshot_version()) == 1
    assert all(int(trace.parent_trace_id) == 0 for trace in evidence.diagnostics_traces)

    with pytest.raises(RuntimeError, match=r"requires use_facade_evidence_producers=True"):
        adapter.build_maintained_worldline_comparison(
            run_id=_RUN_ID,
            episode_id=_EPISODE_ID,
            baseline_deterministic_seed=_SEED,
            candidate_deterministic_seed=_SEED,
            baseline_window_evidence=evidence,
        )
