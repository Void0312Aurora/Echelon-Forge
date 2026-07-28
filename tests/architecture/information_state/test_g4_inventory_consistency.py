"""G4 inventory <-> code consistency gate (Unified Architecture Program T8, slice 5).

The declaration / truth-read-ban / export-parity gates pin the G4 *declarations*
and the C++ export, but nothing pins the maintained T8 register -- the
``t8_g4_truth_leak_inventory`` doc (English canonical + Chinese companion) -- to
the code it describes, nor the declared observation view's public *face
inventory* to its implementation. This gate closes the code->doc half of that
drift seam:

* **Registry -> census.** Every dotted module in the G4 consumer registry (and
  the declared view owner) must exist on disk and appear in the inventory's
  consumer census (as its ``a/b/c.py`` path) in *both* language registers, so a
  consumer cannot be added to (or renamed in) the code registry without the
  register keeping up.
* **Face inventory -> doc (plus ``__all__`` parity).** ``observation_view.__all__``
  equals its three G4 declaration constants plus its public read faces (no export
  drift), and every public face name is documented in both registers, so a face
  cannot be added or renamed in code without the register keeping up.

Direction of enforcement: the *Python code* is the single source of truth, and
the checks run code->doc only -- everything registered or public in code must be
covered by the register. The reverse (doc->code) direction is not enforced: a
register row that goes stale (its consumer removed from the code registry, its
face dropped from the module and ``__all__``), or a fabricated row naming code
that never existed, does not turn this gate red. This is the doc-facing
counterpart to the export-parity gate (which pins the C++ mirror to the Python
declaration).

Everything is static text / AST parsing over source and doc files, so this gate
carries no ``ef_py`` / runtime dependency and stays runnable without a build.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from python.architecture.information_layer import (
    MAINTAINED_INFORMATION_LAYER_CONSUMERS,
    MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
    REQUIRED_DECLARATION_ATTRS,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
_INVENTORY_DIR = REPO_ROOT / "docs" / "plan" / "unified_architecture_program"
_INVENTORY_EN = _INVENTORY_DIR / "t8_g4_truth_leak_inventory.md"
_INVENTORY_ZH = _INVENTORY_DIR / "t8_g4_truth_leak_inventory.zh.md"
_VIEW_OWNER_DOTTED = MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS[0]


def _module_path(dotted: str) -> Path:
    return REPO_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")


def _slash_path(dotted: str) -> str:
    return "/".join(dotted.split(".")) + ".py"


def _module_all(source: str) -> list[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            return [
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    raise AssertionError(f"{_VIEW_OWNER_DOTTED}.__all__ not found")


def _public_defs(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def _documented_identifiers(document: str) -> set[str]:
    """Identifier-like tokens mentioned in ``document``.

    Word-boundary tokenisation, not substring search: a face counts as
    documented only by its own standalone mention. Naive ``face in document``
    matching would let a longer alias silently satisfy a shorter face name --
    ``naval_target_track`` covering ``target_track``, or
    ``support_unit_messages_optional`` covering ``support_unit_messages`` --
    so dropping the shorter face's own row would not turn this gate red.
    """
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", document))


def _undocumented_faces(faces: set[str], document: str) -> list[str]:
    documented = _documented_identifiers(document)
    return sorted(face for face in faces if face not in documented)


def _declaration_constants_present(source: str) -> set[str]:
    tree = ast.parse(source)
    present: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in REQUIRED_DECLARATION_ATTRS:
                    present.add(target.id)
    return present


def test_registered_consumers_and_owner_are_documented_in_both_registers() -> None:
    en = _INVENTORY_EN.read_text(encoding="utf-8")
    zh = _INVENTORY_ZH.read_text(encoding="utf-8")

    for dotted in (
        *MAINTAINED_INFORMATION_LAYER_CONSUMERS,
        *MAINTAINED_INFORMATION_LAYER_VIEW_OWNERS,
    ):
        path = _module_path(dotted)
        assert path.is_file(), f"registered G4 module is missing on disk: {dotted}"
        slash = _slash_path(dotted)
        assert slash in en, (
            f"{slash} is registered in the G4 code registry but not documented in the "
            "English inventory census -- registry and register have drifted"
        )
        assert slash in zh, (
            f"{slash} is registered in the G4 code registry but not documented in the "
            "Chinese inventory census -- registry and register have drifted"
        )


def test_observation_view_all_matches_its_implementation() -> None:
    source = _module_path(_VIEW_OWNER_DOTTED).read_text(encoding="utf-8")
    exported = set(_module_all(source))
    faces = _public_defs(source)
    constants = _declaration_constants_present(source)

    assert constants == set(REQUIRED_DECLARATION_ATTRS), (
        "the declared view owner must carry all three G4 declaration constants; "
        f"missing {sorted(set(REQUIRED_DECLARATION_ATTRS) - constants)}"
    )
    assert exported == faces | constants, (
        "observation_view.__all__ drifted from its implementation "
        f"(only in __all__: {sorted(exported - (faces | constants))}; "
        f"only in module: {sorted((faces | constants) - exported)})"
    )


def test_observation_view_faces_are_documented_in_both_registers() -> None:
    source = _module_path(_VIEW_OWNER_DOTTED).read_text(encoding="utf-8")
    faces = _public_defs(source)
    assert faces, "expected the declared view owner to expose public read faces"

    en = _INVENTORY_EN.read_text(encoding="utf-8")
    zh = _INVENTORY_ZH.read_text(encoding="utf-8")
    missing_en = _undocumented_faces(faces, en)
    missing_zh = _undocumented_faces(faces, zh)

    assert not missing_en, f"view read faces missing from the English inventory: {missing_en}"
    assert not missing_zh, f"view read faces missing from the Chinese inventory: {missing_zh}"


def test_inventory_consistency_gate_is_load_bearing() -> None:
    # Rehearse "a new undocumented face must go red" against an in-memory copy of
    # the view owner, proving both halves are load-bearing. The tree is untouched.
    source = _module_path(_VIEW_OWNER_DOTTED).read_text(encoding="utf-8")
    en = _INVENTORY_EN.read_text(encoding="utf-8")

    # Precondition: the real module is internally consistent.
    assert set(_module_all(source)) == (
        _public_defs(source) | _declaration_constants_present(source)
    )

    injected = source + "\n\ndef leaked_undocumented_face(truth):\n    return truth\n"
    # (a) __all__ / implementation equality must notice the un-exported new def.
    assert set(_module_all(injected)) != (
        _public_defs(injected) | _declaration_constants_present(injected)
    ), "__all__ vs implementation drift gate is not load-bearing"
    # (b) the doc-coverage half must notice the undocumented new face.
    assert _undocumented_faces({"leaked_undocumented_face"}, en) == [
        "leaked_undocumented_face"
    ], "documentation drift gate is not load-bearing"


def test_face_documentation_check_is_not_satisfied_by_a_longer_alias() -> None:
    # The doc-coverage half must resist *alias shadowing*: several real faces are
    # prefixes of other real faces, so a substring check would accept the longer
    # alias as proof that the shorter face is documented, and dropping the
    # shorter face's own row would leave this gate green. Rehearse the actual
    # weakness against in-memory copies of the register with only the standalone
    # mentions stripped -- the aliases stay. The tree is untouched.
    faces = _public_defs(_module_path(_VIEW_OWNER_DOTTED).read_text(encoding="utf-8"))
    shadowed_pairs = [
        (face, alias)
        for face in faces
        for alias in faces
        if alias != face and face in alias
    ]
    assert shadowed_pairs, (
        "expected at least one face name to be a substring of another face name; "
        "if the view's faces were renamed apart, keep this rehearsal by pinning "
        "a synthetic pair instead of deleting it"
    )

    for document in (
        _INVENTORY_EN.read_text(encoding="utf-8"),
        _INVENTORY_ZH.read_text(encoding="utf-8"),
    ):
        # Precondition: with every mention in place, each pair is documented.
        assert not _undocumented_faces({face for face, _ in shadowed_pairs}, document)

        for face, alias in shadowed_pairs:
            # Drop only the shorter face's standalone mentions, keeping every
            # occurrence that is part of the longer alias.
            stripped = re.sub(rf"(?<![A-Za-z0-9_]){face}(?![A-Za-z0-9_])", "", document)
            assert alias in stripped, (
                f"the alias {alias} must survive stripping {face}, otherwise this "
                "rehearsal does not exercise alias shadowing"
            )
            assert _undocumented_faces({face}, stripped) == [face], (
                f"face documentation check accepts the longer alias {alias} as proof "
                f"that {face} is documented -- substring matching has returned"
            )
