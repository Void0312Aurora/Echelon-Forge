"""G4 information-state layer declaration gate (Unified Architecture Program T8).

Enforces Kernel Invariant G4 ("every observation/reward consumer declares its
information-state layer", architecture design doc §15) on the Python-owned
maintained surface:

* Every module in ``MAINTAINED_INFORMATION_LAYER_CONSUMERS`` declares the three
  required G4 constants with authoritative vocabulary (positive gate).
* The facility vocabulary stays byte-pinned to the I32 stage-contract whitelist
  in ``tests/world_batch/test_world_batch_core.py`` and covers every layer/stage
  ``python/rl/runtime/world_batch/core.py`` actually declares, so the T8 and I32
  vocabularies cannot drift apart.
* Removing or corrupting a declaration makes the gate red (negative self-proof),
  so the declarations are load-bearing rather than decorative.

Declarations are read by static AST parsing, so this gate has no import-time
dependency on ``ef_py`` or the consumer modules' runtime behavior.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from python.architecture.information_layer import (
    AUTHORITATIVE_INFORMATION_LAYERS,
    CANONICAL_SEMANTIC_STAGES,
    DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS,
    MAINTAINED_INFORMATION_LAYER_CONSUMERS,
    REQUIRED_DECLARATION_ATTRS,
    VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS,
    validate_information_layer_declaration,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
I32_STAGE_CONTRACT_TEST = (
    REPO_ROOT / "tests" / "world_batch" / "test_world_batch_core.py"
)
# core.py declares BATCH_STEP_STAGES; the gate reads its stage-contract layer /
# stage keyword literals by AST so it never imports the world_batch package
# (whose __init__ pulls ef_py) — the gate stays runnable without a build.
I32_STAGE_CONTRACT_CORE = (
    REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "core.py"
)

# The six-layer / P0-P10 sets, pinned literally here so any edit to the
# production facility is caught independently of the I32 cross-check below.
_PINNED_INFORMATION_LAYERS = {
    "World Truth",
    "Sensed State",
    "Track State",
    "Shared Tactical Picture",
    "Agent Observation",
    "Decision Belief",
}
_PINNED_SEMANTIC_STAGES = {
    "P0 ContentCompile",
    "P1 WorldSetup",
    "P2 TaskingIntent",
    "P3 CommandDelivery",
    "P4 PlatformControl",
    "P5 PhysicsStep",
    "P6 SenseTrackLink",
    "P7 FireControlLaunch",
    "P8 MunitionLifecycle",
    "P9 EffectsDamage",
    "P10 ObservationExport",
}


def _module_path(dotted: str) -> Path:
    return REPO_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")


def _string_tuple_literal(node: ast.AST) -> tuple[str, ...] | None:
    # Tuple-only by design: a G4 declaration is a tuple literal. Accepting
    # ast.List here would let ``INFORMATION_LAYER_CONSUMED = ["World Truth"]``
    # pass the gate while violating the declared tuple contract, so a list
    # literal is rejected (returns None -> treated as a missing declaration).
    if not isinstance(node, ast.Tuple):
        return None
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            out.append(elt.value)
        else:
            return None
    return tuple(out)


def _keyword_string_tuple_values(source: str, keyword_names: set[str]) -> set[str]:
    """Collect string literals from ``StageContract``/``SubStage`` keyword tuples.

    Walks the AST of *source* and gathers every string element of the tuple
    literals passed to the named keyword arguments (e.g. ``semantic_stages=`` /
    ``information_layer_consumed=``). Pure static parsing — no import of the
    world_batch package (which would pull ``ef_py``).
    """
    tree = ast.parse(source)
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.keyword) or node.arg not in keyword_names:
            continue
        values = _string_tuple_literal(node.value)
        if values is not None:
            out.update(values)
    return out


def _module_level_string_tuples(source: str) -> dict[str, tuple[str, ...]]:
    """Map ``name -> (strings,...)`` for module-level string-tuple assignments."""
    tree = ast.parse(source)
    out: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = _string_tuple_literal(node.value)
        if value is None:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = value
    return out


def _set_literal_from_source(source: str, name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return set(ast.literal_eval(node.value))
    raise AssertionError(f"assignment {name!r} not found in source")


def _declaration_violations_for_source(source: str, consumer: str) -> list[str]:
    """Full G4 gate for one consumer's source: presence + vocabulary."""
    declared = _module_level_string_tuples(source)
    missing = [attr for attr in REQUIRED_DECLARATION_ATTRS if attr not in declared]
    if missing:
        return [f"{consumer}: missing G4 declaration constant(s): {missing}"]
    return validate_information_layer_declaration(
        consumed=declared["INFORMATION_LAYER_CONSUMED"],
        produced=declared["INFORMATION_LAYER_PRODUCED"],
        semantic_stage=declared["SEMANTIC_STAGE"],
        consumer=consumer,
    )


def test_facility_vocabulary_is_pinned() -> None:
    assert set(AUTHORITATIVE_INFORMATION_LAYERS) == _PINNED_INFORMATION_LAYERS
    assert set(CANONICAL_SEMANTIC_STAGES) == _PINNED_SEMANTIC_STAGES


def test_facility_vocabulary_matches_i32_stage_contract_whitelist() -> None:
    source = I32_STAGE_CONTRACT_TEST.read_text(encoding="utf-8")
    i32_layers = _set_literal_from_source(source, "_AUTHORITATIVE_INFORMATION_LAYERS")
    i32_stages = _set_literal_from_source(source, "_AUTHORITATIVE_SEMANTIC_STAGES")

    assert set(AUTHORITATIVE_INFORMATION_LAYERS) == i32_layers, (
        "T8 G4 vocabulary drifted from the I32 stage-contract information-layer whitelist"
    )
    assert set(CANONICAL_SEMANTIC_STAGES) == i32_stages, (
        "T8 semantic-stage vocabulary drifted from the I32 stage-contract whitelist"
    )


def test_facility_vocabulary_covers_i32_stage_contract_declarations() -> None:
    source = I32_STAGE_CONTRACT_CORE.read_text(encoding="utf-8")
    used_layers = _keyword_string_tuple_values(
        source, {"information_layer_consumed", "information_layer_produced"}
    )
    used_stages = _keyword_string_tuple_values(source, {"semantic_stages"})

    # Guard against the AST extraction silently returning nothing (which would
    # make the subset assertions vacuously green): core.py declares both.
    assert used_layers, "no stage-contract information layers parsed from core.py"
    assert used_stages, "no stage-contract semantic stages parsed from core.py"

    assert used_layers <= set(AUTHORITATIVE_INFORMATION_LAYERS), (
        f"core.py stage contracts use layers outside the G4 whitelist: "
        f"{sorted(used_layers - set(AUTHORITATIVE_INFORMATION_LAYERS))}"
    )
    assert used_stages <= set(CANONICAL_SEMANTIC_STAGES), (
        f"core.py stage contracts use semantic stages outside the canonical set: "
        f"{sorted(used_stages - set(CANONICAL_SEMANTIC_STAGES))}"
    )


@pytest.mark.parametrize("dotted", MAINTAINED_INFORMATION_LAYER_CONSUMERS)
def test_every_maintained_consumer_declares_valid_g4_layer(dotted: str) -> None:
    path = _module_path(dotted)
    assert path.is_file(), f"registered G4 consumer module is missing: {dotted}"
    violations = _declaration_violations_for_source(
        path.read_text(encoding="utf-8"), dotted
    )
    assert not violations, "\n".join(violations)


def test_maintained_registry_partitions_into_converged_and_deferred() -> None:
    # The declaration gate covers every maintained consumer; the truth-read ban
    # gate (test_g4_truth_read_ban.py) covers only the view-converged subset. Keep
    # the two registries a clean partition so a consumer cannot be silently both
    # migrated and deferred, and so MAINTAINED stays exactly their union (no gap,
    # no overlap). A later slice converges a deferred consumer by moving its path
    # from the deferred tuple into the converged tuple, preserving this union.
    converged = set(VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS)
    deferred = set(DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS)
    assert converged.isdisjoint(deferred), (
        "a consumer cannot be both view-converged and declared-deferred: "
        f"{sorted(converged & deferred)}"
    )
    assert set(MAINTAINED_INFORMATION_LAYER_CONSUMERS) == converged | deferred, (
        "MAINTAINED_INFORMATION_LAYER_CONSUMERS must equal the union of the "
        "view-converged and declared-deferred registries"
    )
    # Both subsets are non-empty at this slice; guard against an accidental empty
    # tuple making the membership/partition checks vacuously green.
    assert converged, "expected a non-empty view-converged consumer set"
    assert deferred, "expected a non-empty declared-deferred consumer set"


def test_declaration_gate_rejects_malformed_declarations() -> None:
    # Non-authoritative layer.
    assert validate_information_layer_declaration(
        consumed=("Godseye Truth",), produced=(), semantic_stage=("P10 ObservationExport",)
    )
    # No layer declared at all.
    assert validate_information_layer_declaration(
        consumed=(), produced=(), semantic_stage=("P10 ObservationExport",)
    )
    # Non-canonical semantic stage.
    assert validate_information_layer_declaration(
        consumed=("World Truth",), produced=(), semantic_stage=("P99 Bogus",)
    )
    # A well-formed declaration produces no violations.
    assert not validate_information_layer_declaration(
        consumed=("World Truth",), produced=("Agent Observation",),
        semantic_stage=("P10 ObservationExport",),
    )


def test_declaration_extractor_requires_tuple_syntax_not_list() -> None:
    # The AST extractor is Tuple-only: a list-literal declaration must be
    # treated as absent (not silently coerced to a tuple), so a maintained
    # consumer cannot satisfy G4 with ``INFORMATION_LAYER_CONSUMED = [...]``.
    list_form = (
        'INFORMATION_LAYER_CONSUMED = ["World Truth"]\n'
        "INFORMATION_LAYER_PRODUCED = ()\n"
        'SEMANTIC_STAGE = ("P10 ObservationExport",)\n'
    )
    assert _string_tuple_literal(ast.parse("['World Truth']").body[0].value) is None
    list_violations = _declaration_violations_for_source(list_form, "list_form")
    assert any("missing G4 declaration" in v for v in list_violations), list_violations

    tuple_form = (
        'INFORMATION_LAYER_CONSUMED = ("World Truth",)\n'
        "INFORMATION_LAYER_PRODUCED = ()\n"
        'SEMANTIC_STAGE = ("P10 ObservationExport",)\n'
    )
    assert _declaration_violations_for_source(tuple_form, "tuple_form") == []


def test_declaration_gate_is_load_bearing_against_a_real_consumer() -> None:
    # Rehearse "removing one declaration must go red" against an in-memory copy
    # of a real registered consumer, proving the enumerating gate above is
    # load-bearing rather than vacuously green.
    dotted = "gym_envs.scenario_loader.reward_runtime.air_combat"
    real_source = _module_path(dotted).read_text(encoding="utf-8")
    assert _declaration_violations_for_source(real_source, dotted) == []

    stripped = real_source.replace("INFORMATION_LAYER_PRODUCED = ()\n", "", 1)
    assert stripped != real_source, "rehearsal precondition: declaration line not found"
    assert _declaration_violations_for_source(stripped, f"{dotted}(stripped)")

    corrupted = real_source.replace(
        'INFORMATION_LAYER_CONSUMED = ("World Truth",)',
        'INFORMATION_LAYER_CONSUMED = ("Godseye Truth",)',
        1,
    )
    assert corrupted != real_source, "rehearsal precondition: layer literal not found"
    assert _declaration_violations_for_source(corrupted, f"{dotted}(corrupted)")
