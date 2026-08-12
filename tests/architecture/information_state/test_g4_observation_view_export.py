"""G4 observation-view export parity gate (Unified Architecture Program T8, slice 4).

The first three T8 slices declared each maintained consumer's information-state
layer, materialized a declared observation view on the TL13 read seam
(``gym_envs/observation_view.py``), and migrated consumers onto it. This fourth
slice makes "what layer the TL13 seam produces" a *runtime-queryable* fact: the
C++ runtime facade now exports a declared ``ObservationViewSpec`` via
``RuntimeFacade::describe_maintained_observation_view`` (I60).

This gate ratchets that export:

* **Export parity (single source of truth).** The C++ export mirrors only the
  *structural facts* of the maintained observation view -- its view id and the
  produced / consumed information-state layers and semantic stage -- from the
  Python single source of truth (``gym_envs/observation_view.py``). This gate
  fails if the C++ mirror drifts from the Python registry, so mirroring the
  strings into C++ cannot silently diverge. The detailed observation field list
  stays Python-owned (the export's ``required_fields`` / ``optional_fields`` are
  deliberately empty), so there is no dual-source field catalogue to drift.
* **G4 vocabulary.** The exported layers/stage use only the authoritative
  six-layer / P0-P10 whitelist.
* **Load-bearing.** The pure parity checker goes red on injected drift, so the
  gate is not vacuously green.
* **Bounded wiring.** I87 reads the export exactly once from the same facade at
  adapter construction when explicitly enabled. The default path and TL13 seam
  never call it, and no C++ runtime path is rewired.

The ef_py-dependent parity/value tests skip when no local build is available
(matching the repo's ef_py skip convention); the load-bearing and wiring-boundary
tests are pure text/AST and always run.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from python.architecture.information_layer import (
    AUTHORITATIVE_INFORMATION_LAYERS,
    CANONICAL_SEMANTIC_STAGES,
    MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
    observation_view_export_parity_violations,
    read_maintained_observation_view_export,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
_EXPORT_SYMBOL = "describe_maintained_observation_view"

# Sites where the export symbol is allowed to appear: its declaration, its
# implementation, and its binding. Anywhere else would be wiring it into an
# existing path.
_ALLOWED_EXPORT_SITES = frozenset(
    {
        "src/runtime/facade/runtime_facade.h",
        "src/runtime/facade/runtime_facade_query.cpp",
        # The RuntimeFacade binding slice; bindings_runtime.cpp is an
        # orchestrator shell since the per-domain decomposition.
        "src/interfaces/python/bindings_runtime_facade.cpp",
    }
)


# --- ef_py availability (skip without a local build) --------------------------
try:  # pragma: no cover - import guard exercised by environment, not logic
    from python.runtime_bootstrap import configure_repo_imports

    configure_repo_imports()
    import ef_py  # noqa: F401

    _EF_PY_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - only when ef_py is unbuilt
    ef_py = None  # type: ignore[assignment]
    _EF_PY_ERROR = exc

requires_ef_py = pytest.mark.skipif(
    ef_py is None,
    reason=f"ef_py runtime binding is unavailable in the active interpreter: {_EF_PY_ERROR}",
)


def _registry_declaration() -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """The Python single source of truth: the view owner's G4 declaration.

    ``gym_envs`` is a namespace package (no ``__init__``) and the view owner is
    stdlib-only, so importing it needs no build.
    """
    from gym_envs import observation_view

    return (
        MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS[0],
        tuple(observation_view.INFORMATION_LAYER_CONSUMED),
        tuple(observation_view.INFORMATION_LAYER_PRODUCED),
        tuple(observation_view.SEMANTIC_STAGE),
    )


# --- Export parity: C++ export == Python registry ----------------------------
@requires_ef_py
def test_cpp_export_matches_python_registry_single_source_of_truth() -> None:
    export = read_maintained_observation_view_export()
    view_id, consumed, produced, semantic_stage = _registry_declaration()

    violations = observation_view_export_parity_violations(
        export,
        expected_view_id=view_id,
        expected_consumed=consumed,
        expected_produced=produced,
        expected_semantic_stage=semantic_stage,
    )
    assert not violations, "\n".join(violations)


@requires_ef_py
def test_cpp_export_field_values_and_python_owned_field_list_stays_empty() -> None:
    spec = ef_py.RuntimeFacade(0).describe_maintained_observation_view()

    assert spec.view_id == "gym_envs.observation_view"
    assert tuple(spec.information_layer_produced) == ("Agent Observation",)
    assert tuple(spec.information_layer_consumed) == (
        "World Truth",
        "Track State",
        "Shared Tactical Picture",
    )
    assert tuple(spec.semantic_stage) == ("P10 ObservationExport",)
    # schema_version keeps the DTO default (its single source is the .inc).
    assert spec.schema_version == "1.0"

    # Single-source strategy: the detailed observation field catalogue stays
    # Python-owned, so the C++ structural-fact export leaves these empty rather
    # than duplicating a field list that could drift from the Python side.
    assert list(spec.required_fields) == []
    assert list(spec.optional_fields) == []


@requires_ef_py
def test_cpp_export_uses_only_g4_authoritative_vocabulary() -> None:
    export = read_maintained_observation_view_export()

    layers = set(export["information_layer_produced"]) | set(
        export["information_layer_consumed"]
    )
    assert layers <= set(AUTHORITATIVE_INFORMATION_LAYERS), (
        f"C++ export uses layers outside the G4 whitelist: "
        f"{sorted(layers - set(AUTHORITATIVE_INFORMATION_LAYERS))}"
    )
    assert set(export["semantic_stage"]) <= set(CANONICAL_SEMANTIC_STAGES), (
        f"C++ export uses semantic stages outside the canonical set: "
        f"{sorted(set(export['semantic_stage']) - set(CANONICAL_SEMANTIC_STAGES))}"
    )


@requires_ef_py
def test_cpp_export_is_a_deterministic_constant_independent_of_facade_state() -> None:
    # The export is a pure constant producer: identical across repeated calls and
    # across facades with different world counts, proving it reads no facade
    # instance state and so cannot couple to (or perturb) run behavior.
    a = ef_py.RuntimeFacade(0).describe_maintained_observation_view()
    b = ef_py.RuntimeFacade(4).describe_maintained_observation_view()

    for spec in (a, b):
        assert tuple(spec.information_layer_produced) == ("Agent Observation",)
        assert tuple(spec.information_layer_consumed) == (
            "World Truth",
            "Track State",
            "Shared Tactical Picture",
        )
        assert tuple(spec.semantic_stage) == ("P10 ObservationExport",)
        assert spec.view_id == "gym_envs.observation_view"


# --- Load-bearing self-proof for the pure parity checker ----------------------
def test_parity_gate_is_load_bearing() -> None:
    view_id, consumed, produced, semantic_stage = _registry_declaration()
    expected = {
        "expected_view_id": view_id,
        "expected_consumed": consumed,
        "expected_produced": produced,
        "expected_semantic_stage": semantic_stage,
    }
    good = {
        "schema_version": "1.0",
        "view_id": view_id,
        "information_layer_produced": produced,
        "information_layer_consumed": consumed,
        "semantic_stage": semantic_stage,
    }
    assert observation_view_export_parity_violations(good, **expected) == []

    # Drift in each mirrored dimension must go red.
    assert observation_view_export_parity_violations(
        {**good, "view_id": "gym_envs.some_other_owner"}, **expected
    )
    assert observation_view_export_parity_violations(
        {**good, "information_layer_produced": ("Decision Belief",)}, **expected
    )
    assert observation_view_export_parity_violations(
        {**good, "information_layer_consumed": ("World Truth",)}, **expected
    )
    assert observation_view_export_parity_violations(
        {**good, "semantic_stage": ("P2 TaskingIntent",)}, **expected
    )
    # A non-authoritative layer fails the vocabulary half even before equality.
    assert observation_view_export_parity_violations(
        {**good, "information_layer_produced": ("Godseye Truth",)}, **expected
    )


# --- Wiring boundary: construction-only I87 opt-in ---------------------------
def test_export_symbol_is_wired_only_at_the_declared_construction_boundary() -> None:
    # The declaration must be a read-only const method.
    header = (REPO_ROOT / "src/runtime/facade/runtime_facade.h").read_text(
        encoding="utf-8"
    )
    assert (
        f"ObservationViewSpec {_EXPORT_SYMBOL}() const;" in header
    ), "export must be declared as a read-only const method"

    # (1) No C++ facade translation unit other than the impl references the
    # symbol -> no existing export/step/window/packet/counterfactual path calls
    # it.
    for path in sorted((REPO_ROOT / "src" / "runtime" / "facade").glob("*.cpp")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if rel in _ALLOWED_EXPORT_SITES:
            assert _EXPORT_SYMBOL in text, f"expected the export symbol in {rel}"
            continue
        assert _EXPORT_SYMBOL not in text, (
            f"{rel} references {_EXPORT_SYMBOL!r}: this slice must not wire the "
            "export into any existing runtime path"
        )

    # (2) The symbol is bound exactly where expected and nowhere else in the
    # binding layer.
    for path in sorted((REPO_ROOT / "src" / "interfaces" / "python").glob("*.cpp")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        present = _EXPORT_SYMBOL in path.read_text(encoding="utf-8")
        assert present == (rel in _ALLOWED_EXPORT_SITES), (
            f"unexpected {_EXPORT_SYMBOL!r} presence in {rel}"
        )

    # (3) No gym_envs consumer (including the TL13 seam) calls the export. The
    # I87 opt-in is deliberately owned by the higher-level Python adapter, not
    # by the TL13 seam or a lower observation consumer.
    for path in sorted((REPO_ROOT / "gym_envs").rglob("*.py")):
        assert _EXPORT_SYMBOL not in path.read_text(encoding="utf-8"), (
            f"{path.relative_to(REPO_ROOT).as_posix()} references the export; the "
            "TL13 seam and its consumers must stay unchanged"
        )

    # (4) I87 has exactly one Python call site: the adapter's construction-time
    # opt-in. Keeping this assertion narrow makes the default-off describe count
    # and the single-facade ownership boundary visible to the architecture gate.
    adapter_path = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
    adapter_text = adapter_path.read_text(encoding="utf-8")
    adapter_tree = ast.parse(adapter_text)
    adapter_calls = [
        node
        for node in ast.walk(adapter_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == _EXPORT_SYMBOL
    ]
    assert len(adapter_calls) == 1, (
        "I87 must read the maintained ObservationViewSpec export exactly once "
        "through RuntimeFacadeAdapter construction"
    )
    for path in sorted((REPO_ROOT / "python" / "rl").rglob("*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if rel == "python/rl/runtime/world_batch/adapter.py":
            continue
        assert _EXPORT_SYMBOL not in text, (
            f"{rel} references {_EXPORT_SYMBOL!r}: keep the I87 export read in "
            "the adapter construction boundary"
        )


def test_tl13_seam_behavior_is_unchanged() -> None:
    # The TL13 read chokepoint keeps its exact pre-slice returns; the export is a
    # separate additive producer, not a rewrite of the seam.
    seam = (REPO_ROOT / "gym_envs" / "scenario_loader" / "core.py").read_text(
        encoding="utf-8"
    )
    assert "return self.sim.get_agent_observation(resolved_agent_id)" in seam
    assert "return self.sim.get_instrument_state(resolved_agent_id)" in seam
    assert _EXPORT_SYMBOL not in seam
