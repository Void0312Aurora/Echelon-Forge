"""G4 truth-read-ban gate (Unified Architecture Program T8, second slice).

The first T8 slice made every maintained observation/reward consumer *declare*
its information-state layer; the second slice materializes a declared observation
view on the TL13 read seam and migrates the consumers to read through it. This
gate ratchets that convergence:

* Every module in ``VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS`` must contain no
  raw World-Truth attribute read (``truth.<attr>`` or ``getattr(truth, ...)``):
  the reads now flow through the declared view owner. This is the AST truth-read
  ban that G4 anticipates ("enforcement moves from documentation to AST gates",
  design doc §15), scoped to the migrated surface.
* The declared view owner(s) in ``MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS`` are
  the read owner and are excluded from the ban; each must still carry a valid G4
  declaration (a read owner is allowed to read truth, consumers are not).
* The declared-but-deferred consumers in
  ``DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS`` (T8 third slice, I56) carry a
  G4 declaration but are not yet view-converged, so they are excluded from the ban
  scan. The gate proves each still performs raw truth reads, so the exclusion is a
  real deferral (not an accidentally-clean module) and converging one later forces
  moving it into the ban-gated converged set.
* An explicit inline diagnostic marker exempts a single read, so a legitimate
  declared diagnostic truth read stays possible without weakening the ban.
* The gate proves it is load-bearing: injecting a raw truth read into an
  in-memory copy of a real migrated consumer goes red.

Everything is static AST / text parsing over source files, so this gate carries
no ``ef_py`` / runtime dependency and stays runnable without a build.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from python.architecture.information_layer import (
    DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS,
    MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
    REQUIRED_DECLARATION_ATTRS,
    VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS,
    validate_information_layer_declaration,
)


REPO_ROOT = Path(__file__).resolve().parents[3]

# Inline marker that exempts a single raw truth read as an explicitly declared
# diagnostic read (design doc §15: diagnostics may read truth directly).
_DIAGNOSTIC_ALLOW_MARKER = "g4-diagnostic-truth-read"

# The World-Truth policy-observation object is named ``truth`` throughout the
# maintained consumers (it is the object returned by the TL13 seam
# ``get_policy_agent_observation``); the ban keys off that name.
_TRUTH_NAMES = frozenset({"truth"})


def _module_path(dotted: str) -> Path:
    return REPO_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")


def _module_source(dotted: str) -> str:
    return _module_path(dotted).read_text(encoding="utf-8")


def _raw_truth_read_lines(source: str) -> list[int]:
    """Return sorted line numbers of raw World-Truth reads not marked diagnostic.

    Detects two forms: attribute access on a Name in :data:`_TRUTH_NAMES`
    (``truth.<attr>``) and ``getattr(<truth-name>, ...)`` calls. A flagged line
    whose source text carries :data:`_DIAGNOSTIC_ALLOW_MARKER` is exempt.
    """
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


def _module_level_string_tuples(source: str) -> dict[str, tuple[str, ...]]:
    tree = ast.parse(source)
    out: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Tuple):
            continue
        values: list[str] = []
        ok = True
        for elt in node.value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.append(elt.value)
            else:
                ok = False
                break
        if not ok:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = tuple(values)
    return out


def _declaration_violations(source: str, consumer: str) -> list[str]:
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


def test_view_owner_declares_valid_g4_layer() -> None:
    assert MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS, "no declared observation-view owner registered"
    for dotted in MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS:
        path = _module_path(dotted)
        assert path.is_file(), f"declared observation-view owner module is missing: {dotted}"
        violations = _declaration_violations(path.read_text(encoding="utf-8"), dotted)
        assert not violations, "\n".join(violations)


@pytest.mark.parametrize("dotted", VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS)
def test_migrated_consumer_has_no_raw_truth_reads(dotted: str) -> None:
    path = _module_path(dotted)
    assert path.is_file(), f"view-converged consumer module is missing: {dotted}"
    flagged = _raw_truth_read_lines(path.read_text(encoding="utf-8"))
    assert not flagged, (
        f"{dotted}: raw World-Truth reads must flow through the declared observation view "
        f"(gym_envs.observation_view); found raw truth reads at line(s) {flagged}"
    )


def test_truth_read_ban_is_load_bearing() -> None:
    # Rehearse "injecting a raw truth read must go red" against an in-memory copy
    # of a real migrated consumer, proving the enumerating gate above is not
    # vacuously green. The working tree is never modified.
    dotted = "gym_envs.scenario_loader.reward_runtime.safety"
    real_source = _module_source(dotted)
    assert _raw_truth_read_lines(real_source) == [], (
        f"precondition: {dotted} should carry no raw truth reads after migration"
    )

    anchor = "    inputs.finite_state_valid = bool(finite_state_valid)\n"
    assert anchor in real_source, "rehearsal precondition: anchor line not found"

    attr_form = real_source.replace(anchor, anchor + "    _leaked = truth.health\n", 1)
    assert _raw_truth_read_lines(attr_form), "gate failed to flag an injected truth.<attr> read"

    getattr_form = real_source.replace(
        anchor, anchor + '    _leaked = getattr(truth, "health", 0.0)\n', 1
    )
    assert _raw_truth_read_lines(getattr_form), "gate failed to flag an injected getattr(truth, ...) read"


def test_diagnostic_marker_whitelists_a_single_truth_read() -> None:
    # The diagnostic allow marker exempts exactly the marked read, so a declared
    # diagnostic truth read stays possible without weakening the ban elsewhere.
    source = (
        "def probe(truth):\n"
        "    a = truth.x\n"
        f"    b = truth.y  # {_DIAGNOSTIC_ALLOW_MARKER}: intentional diagnostic probe\n"
        "    return a, b\n"
    )
    assert _raw_truth_read_lines(source) == [2]


@pytest.mark.parametrize("dotted", DECLARED_DEFERRED_INFORMATION_LAYER_CONSUMERS)
def test_declared_deferred_consumer_is_excluded_from_ban_and_keeps_raw_reads(dotted: str) -> None:
    # The T8 third slice (I56) declared these consumers' information layer but did
    # not converge their reads onto the observation view. Prove (a) each is
    # excluded from the ban scan set (so its intentional raw reads are allowed) and
    # (b) it genuinely still performs raw truth reads -- so the deferral is real
    # and this stays load-bearing: if a later slice converges one (removing its raw
    # reads) without moving it into VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS, this
    # goes red and forces the reclassification.
    assert dotted not in VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS, (
        f"declared-deferred consumer {dotted} must not be in the truth-read-ban scan set"
    )
    path = _module_path(dotted)
    assert path.is_file(), f"declared-deferred consumer module is missing: {dotted}"
    flagged = _raw_truth_read_lines(_module_source(dotted))
    assert flagged, (
        f"{dotted}: expected raw World-Truth reads (declared-but-deferred, not yet "
        "view-converged); found none -- if it converged, move it into "
        "VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS so the ban gate covers it"
    )


def test_view_owner_reads_truth_and_is_excluded_from_ban() -> None:
    # The declared read owner is exactly where raw truth reads legitimately live.
    # Prove (a) it is excluded from the scanned converged-consumer set and (b) it
    # actually performs raw truth reads, so the ban would fire if it were scanned.
    for dotted in MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS:
        assert dotted not in VIEW_CONVERGED_INFORMATION_LAYER_CONSUMERS, (
            f"declared read owner {dotted} must not be in the truth-read-ban scan set"
        )
        owner_flags = _raw_truth_read_lines(_module_source(dotted))
        assert owner_flags, (
            f"{dotted}: the declared read owner is expected to own the raw truth reads; "
            "none found (did the owner stop owning them?)"
        )
