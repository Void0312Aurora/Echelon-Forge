"""G4 per-file maintained-consumer classification gate (Unified Architecture Program T8).

The I63 gate-net hardening closed the "new unregistered raw-truth-read consumer"
escape only for ``gym_envs/scenario_loader/reward_runtime/**`` and recorded the
broader observation surfaces as an open escape hatch: those directories
interleave legitimate non-consumer truth readers (command / action / loading /
behavior paths), so a bare directory-level scan would false-positive there.
This gate (this iteration) closes that recorded escape hatch:

* It AST-scans the whole maintained surface
  (:data:`python.architecture.consumer_classification.SCANNED_SURFACE_PACKAGES`
  -- ``gym_envs/**`` and ``python/rl/**``, a strict superset of the I63
  ``reward_runtime/`` scan) for raw World-Truth reads (``truth.<attr>`` and
  ``getattr(truth, ...)``, minus reads carrying the inline diagnostic marker).
* Every hit must have a per-file classification row in
  :data:`python.architecture.consumer_classification.MAINTAINED_TRUTH_READER_CLASSIFICATION`,
  and every row must still correspond to a real hit (no stale rows), so the
  registry and the code agree exactly in both directions.
* Classification lies are caught where structurally checkable: a file whose G4
  declaration includes ``P10 ObservationExport`` cannot be labeled a
  command/loading/diagnostics reader, and a command-stage declarer cannot be
  labeled an observation/reward consumer.
* Tamper rehearsals prove the gate is load-bearing: an injected unregistered
  consumer goes red, a classification lie goes red, and a stale row goes red --
  all against in-memory copies; the working tree is never modified.

The raw-truth-read pattern vocabulary is deliberately REIMPLEMENTED here rather
than imported from ``test_g4_truth_read_ban.py``: architecture gates do not
import from each other's test modules (each stays independently runnable and
independently tamperable), and a shared-vocabulary parity test below keeps the
two local copies from drifting apart semantically.

Everything is static AST / text parsing over source files, so this gate carries
no ``ef_py`` / runtime dependency and stays runnable without a build.
"""

from __future__ import annotations

import ast
from pathlib import Path

from python.architecture.consumer_classification import (
    COMMAND_ACTION_LOADING_READER,
    CONSUMER_CLASSIFICATION_CATEGORIES,
    DECLARED_VIEW_OWNER,
    DIAGNOSTICS,
    G4_DECLARATION_PENDING_CONSUMERS,
    MAINTAINED_TRUTH_READER_CLASSIFICATION,
    OBSERVATION_CONSUMER,
    OBSERVATION_EXPORT_STAGE,
    OBSERVATION_REWARD_CONSUMER_CATEGORIES,
    REWARD_CONSUMER,
    SCANNED_SURFACE_EXCLUDED_PARTS,
    SCANNED_SURFACE_PACKAGES,
    classification_violations,
)
from python.architecture.information_layer import (
    CANONICAL_SEMANTIC_STAGES,
    MAINTAINED_INFORMATION_LAYER_CONSUMERS,
    MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
)


REPO_ROOT = Path(__file__).resolve().parents[3]

# --- Raw-truth-read scan (local reimplementation of the ban-gate vocabulary) --
# Same pattern vocabulary as the G4 truth-read-ban gate: attribute access on a
# name in _TRUTH_NAMES, getattr(<truth-name>, ...), and the inline diagnostic
# allow marker exempting a single marked read. Kept local by design (see module
# docstring); test_pattern_vocabulary_matches_the_ban_gate pins the parity.

_DIAGNOSTIC_ALLOW_MARKER = "g4-diagnostic-truth-read"
_TRUTH_NAMES = frozenset({"truth"})


def _raw_truth_read_lines(source: str) -> list[int]:
    tree = ast.parse(source)
    source_lines = source.splitlines()
    flagged: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in _TRUTH_NAMES
        ):
            flagged.add(node.lineno)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in _TRUTH_NAMES
        ):
            flagged.add(node.lineno)
    allowed = {
        lineno
        for lineno in flagged
        if 1 <= lineno <= len(source_lines)
        and _DIAGNOSTIC_ALLOW_MARKER in source_lines[lineno - 1]
    }
    return sorted(flagged - allowed)


# --- Surface enumeration ------------------------------------------------------

def _dotted_from_repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).with_suffix("").as_posix().replace("/", ".")


def _scanned_surface_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for package in SCANNED_SURFACE_PACKAGES:
        package_root = REPO_ROOT / Path(package)
        assert package_root.is_dir(), f"scanned surface package missing: {package}"
        for path in sorted(package_root.rglob("*.py")):
            if any(part in SCANNED_SURFACE_EXCLUDED_PARTS for part in path.parts):
                continue
            sources[_dotted_from_repo_path(path)] = path.read_text(encoding="utf-8")
    return sources


def _raw_truth_readers(sources: dict[str, str]) -> list[str]:
    return sorted(dotted for dotted, source in sources.items() if _raw_truth_read_lines(source))


def _module_level_string_tuple(source: str, name: str) -> tuple[str, ...] | None:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Tuple):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        values: list[str] = []
        for elt in node.value.elts:
            if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
                return None
            values.append(elt.value)
        return tuple(values)
    return None


def _declared_semantic_stages(sources: dict[str, str]) -> dict[str, tuple[str, ...]]:
    stages: dict[str, tuple[str, ...]] = {}
    for dotted, source in sources.items():
        declared = _module_level_string_tuple(source, "SEMANTIC_STAGE")
        if declared is not None:
            stages[dotted] = declared
    return stages


def _real_violations(sources: dict[str, str]) -> list[str]:
    return classification_violations(
        raw_truth_readers=_raw_truth_readers(sources),
        classification=MAINTAINED_TRUTH_READER_CLASSIFICATION,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=_declared_semantic_stages(sources),
    )


# --- Vacuity guards -----------------------------------------------------------

def test_scan_surface_covers_known_anchor_modules() -> None:
    # Guard against a vacuous scan (package renamed/moved): known truth readers
    # from every corner of the surface must be present, so the gate cannot pass
    # by silently scanning nothing.
    sources = _scanned_surface_sources()
    for anchor in (
        "gym_envs.observation_view",
        "gym_envs.scenario_loader.step_evaluation",
        "gym_envs.scenario_loader.reward_runtime.safety",
        "python.rl.tasking.leader_tasking",
        "python.rl.runtime.world_batch.vec_env",
    ):
        assert anchor in sources, f"maintained-surface scan missed {anchor}"


def test_pattern_vocabulary_matches_the_ban_gate() -> None:
    # The scan vocabulary is reimplemented locally (not imported from the ban
    # gate's test module); this parity check pins the two copies to the same
    # semantics: both truth-read forms are flagged, and the inline diagnostic
    # marker exempts exactly the marked line.
    source = (
        "def probe(truth):\n"
        "    a = truth.x\n"
        '    b = getattr(truth, "y", 0.0)\n'
        f"    c = truth.z  # {_DIAGNOSTIC_ALLOW_MARKER}: intentional diagnostic probe\n"
        "    return a, b, c\n"
    )
    assert _raw_truth_read_lines(source) == [2, 3]


def test_observation_export_stage_literal_is_authoritative() -> None:
    # The classification module keeps the P10 stage string as a local literal
    # (stdlib-only, no cross-module import); pin it to the authoritative
    # semantic-stage vocabulary so it cannot silently drift.
    assert OBSERVATION_EXPORT_STAGE in CANONICAL_SEMANTIC_STAGES


# --- The gate itself ----------------------------------------------------------

def test_every_maintained_raw_truth_reader_is_classified() -> None:
    sources = _scanned_surface_sources()
    readers = _raw_truth_readers(sources)
    # The declared view owner reads truth by design; if this ever comes up
    # empty the scan itself is broken, not the surface clean.
    assert "gym_envs.observation_view" in readers, (
        "scan sanity: the declared observation-view owner must appear as a raw truth reader"
    )
    violations = _real_violations(sources)
    assert not violations, "\n".join(violations)


def test_classification_registry_rows_point_at_real_files() -> None:
    for dotted, category in MAINTAINED_TRUTH_READER_CLASSIFICATION.items():
        assert category in CONSUMER_CLASSIFICATION_CATEGORIES, (
            f"{dotted}: unknown category {category!r}"
        )
        path = REPO_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")
        assert path.is_file(), f"classified module is missing on disk: {dotted}"


def test_g4_registered_deferred_consumers_are_all_classified() -> None:
    # Every G4-registered consumer that still performs raw truth reads (the
    # declared-but-deferred set) must carry a classification row; converged
    # consumers read via the view and correctly have no row.
    sources = _scanned_surface_sources()
    readers = set(_raw_truth_readers(sources))
    for dotted in MAINTAINED_INFORMATION_LAYER_CONSUMERS:
        if dotted in readers:
            assert dotted in MAINTAINED_TRUTH_READER_CLASSIFICATION, (
                f"G4-registered consumer {dotted} reads raw truth but is unclassified"
            )


# --- Tamper rehearsals (in-memory only; the working tree is never modified) ---

def test_injected_unregistered_consumer_goes_red() -> None:
    # Rehearse the escape this gate exists to close: a new file with raw truth
    # reads dropped onto the maintained surface without a classification row.
    sources = _scanned_surface_sources()
    injected_dotted = "gym_envs.universal_env_parts.injected_shadow_consumer"
    assert injected_dotted not in sources
    assert injected_dotted not in MAINTAINED_TRUTH_READER_CLASSIFICATION
    tampered = {
        **sources,
        injected_dotted: "def leak(truth):\n    return truth.health\n",
    }
    violations = classification_violations(
        raw_truth_readers=_raw_truth_readers(tampered),
        classification=MAINTAINED_TRUTH_READER_CLASSIFICATION,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=_declared_semantic_stages(tampered),
    )
    assert any(injected_dotted in v for v in violations), (
        "gate failed to flag an injected unregistered raw-truth-read consumer"
    )
    # Classifying the injected file clears it: the gate is keyed on registry
    # membership, not merely on the presence of a raw read.
    classified = {
        **MAINTAINED_TRUTH_READER_CLASSIFICATION,
        injected_dotted: COMMAND_ACTION_LOADING_READER,
    }
    cleared = classification_violations(
        raw_truth_readers=_raw_truth_readers(tampered),
        classification=classified,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=_declared_semantic_stages(tampered),
    )
    assert not any(injected_dotted in v for v in cleared), (
        "classification row failed to clear the injected consumer"
    )


def test_classification_lie_on_a_p10_declarer_goes_red() -> None:
    # Labeling an observation/reward consumer as a loading reader must be
    # caught: step_evaluation declares SEMANTIC_STAGE including P10
    # ObservationExport, which structurally pins its consumer role.
    sources = _scanned_surface_sources()
    liar = "gym_envs.scenario_loader.step_evaluation"
    stages = _declared_semantic_stages(sources)
    assert OBSERVATION_EXPORT_STAGE in stages[liar], (
        "rehearsal precondition: step_evaluation declares the P10 stage"
    )
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[liar] = COMMAND_ACTION_LOADING_READER
    violations = classification_violations(
        raw_truth_readers=_raw_truth_readers(sources),
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
    )
    assert any(liar in v and COMMAND_ACTION_LOADING_READER in v for v in violations), (
        "gate failed to catch an observation/reward consumer mislabeled as a loading reader"
    )


def test_reverse_lie_on_a_command_stage_declarer_goes_red() -> None:
    # The symmetric lie: the scripted C2 leader director declares only command
    # stages (no P10), so labeling it an observation consumer must be caught.
    sources = _scanned_surface_sources()
    liar = "python.rl.tasking.leader_tasking"
    stages = _declared_semantic_stages(sources)
    assert OBSERVATION_EXPORT_STAGE not in stages[liar], (
        "rehearsal precondition: leader_tasking declares no P10 stage"
    )
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[liar] = OBSERVATION_CONSUMER
    violations = classification_violations(
        raw_truth_readers=_raw_truth_readers(sources),
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
    )
    assert any(liar in v and OBSERVATION_CONSUMER in v for v in violations), (
        "gate failed to catch a command-stage reader mislabeled as an observation consumer"
    )


def test_stale_classification_row_goes_red() -> None:
    # A row whose file no longer performs raw truth reads (converged or
    # deleted) must be pruned; rehearse with a real converged consumer that
    # correctly has no row today.
    sources = _scanned_surface_sources()
    converged = "gym_envs.scenario_loader.reward_runtime.safety"
    assert converged in sources and not _raw_truth_read_lines(sources[converged]), (
        "rehearsal precondition: the converged reward consumer holds no raw truth reads"
    )
    assert converged not in MAINTAINED_TRUTH_READER_CLASSIFICATION
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[converged] = REWARD_CONSUMER
    violations = classification_violations(
        raw_truth_readers=_raw_truth_readers(sources),
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=_declared_semantic_stages(sources),
    )
    assert any(converged in v for v in violations), (
        "gate failed to flag a stale classification row for a converged consumer"
    )


def test_view_owner_misclassification_goes_red() -> None:
    sources = _scanned_surface_sources()
    owner = MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS[0]
    readers = _raw_truth_readers(sources)
    stages = _declared_semantic_stages(sources)

    # (a) The declared read owner labeled as a plain consumer.
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[owner] = OBSERVATION_CONSUMER
    violations = classification_violations(
        raw_truth_readers=readers,
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
    )
    assert any(owner in v and DECLARED_VIEW_OWNER in v for v in violations), (
        "gate failed to catch the declared view owner classified as a plain consumer"
    )

    # (b) A non-owner claiming the view-owner classification.
    pretender = "gym_envs.scenario_loader.step_evaluation"
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[pretender] = DECLARED_VIEW_OWNER
    violations = classification_violations(
        raw_truth_readers=readers,
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
    )
    assert any(pretender in v and DECLARED_VIEW_OWNER in v for v in violations), (
        "gate failed to catch a non-owner claiming the view-owner classification"
    )


def test_registered_consumer_cannot_hide_as_diagnostics() -> None:
    sources = _scanned_surface_sources()
    liar = "gym_envs.scenario_loader.navigation_runtime.guidance"
    assert liar in MAINTAINED_INFORMATION_LAYER_CONSUMERS
    tampered_registry = dict(MAINTAINED_TRUTH_READER_CLASSIFICATION)
    tampered_registry[liar] = DIAGNOSTICS
    violations = classification_violations(
        raw_truth_readers=_raw_truth_readers(sources),
        classification=tampered_registry,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=_declared_semantic_stages(sources),
    )
    assert any(liar in v and DIAGNOSTICS in v for v in violations), (
        "gate failed to catch a G4-registered consumer hidden behind a diagnostics label"
    )


def test_pending_declaration_pin_is_load_bearing_in_both_directions() -> None:
    # The unregistered observation/reward consumers are pinned exactly:
    # (a) dropping a pin while the consumer stays classified-but-unregistered
    # goes red, and (b) a stale pin (consumer became G4-registered) goes red.
    sources = _scanned_surface_sources()
    readers = _raw_truth_readers(sources)
    stages = _declared_semantic_stages(sources)
    pending = "python.rl.runtime.world_batch.observation_batching"
    assert pending in G4_DECLARATION_PENDING_CONSUMERS

    shrunk = tuple(d for d in G4_DECLARATION_PENDING_CONSUMERS if d != pending)
    violations = classification_violations(
        raw_truth_readers=readers,
        classification=MAINTAINED_TRUTH_READER_CLASSIFICATION,
        g4_registered_consumers=MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
        declaration_pending=shrunk,
    )
    assert any(pending in v for v in violations), (
        "gate failed to demand a pin (or a G4 registration) for an unregistered consumer"
    )

    violations = classification_violations(
        raw_truth_readers=readers,
        classification=MAINTAINED_TRUTH_READER_CLASSIFICATION,
        g4_registered_consumers=(*MAINTAINED_INFORMATION_LAYER_CONSUMERS, pending),
        g4_view_owners=MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
        declared_semantic_stages=stages,
    )
    assert any(pending in v and "stale pin" in v for v in violations), (
        "gate failed to flag a stale pending pin after the consumer became G4-registered"
    )
