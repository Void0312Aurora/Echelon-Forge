"""Spec-driven anti-drift gate for the flight-dynamics tuning X-macro bundles.

``AeroTuning`` (I66) and ``EngineTuning`` (the iteration after it) landed as
two hand-expansions of one template: the same three-leg anchor discipline, the
same residue belts, the same tamper drills, differing only in which struct
they anchor to, how many macro families the list needs, how many include
passes the helper makes, and which member the adjudication holds back.

``TuningBundleSpec`` carries those differences; the checkers below carry the
judgment, once.

What must NOT be flattened away by the parameterisation is *why* each bundle's
absence set looks the way it does -- that reasoning is the reviewable part of
the gate, not the key list. It travels verbatim in ``TuningBundleSpec``'s
``rationale``, ``anchor_notes``, ``allowed_types_reason``,
``expected_passes_reason`` and ``held_read_reason`` fields, and the spec
refuses to be constructed with a stub rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tests.support.xmacro_gate import (
    WorktreeAnchor,
    function_body,
    parse_inc_fields,
    struct_members_line_scan,
)


# The shortest rationale that can still carry an adjudication rather than a
# label. Both landed bundles are far above it; the floor exists so a future
# bundle cannot be added with `rationale="held"`.
MIN_RATIONALE_CHARS = 80


@dataclass(frozen=True)
class TextTamper:
    """One literal ``old -> new`` substitution driving a tamper drill.

    ``apply`` asserts the substitution actually landed, so a drill can never
    silently degrade into "tampered nothing, gate stayed green" after the
    pinned text moves.
    """

    old: str
    new: str

    def apply(self, text: str) -> str:
        tampered = text.replace(self.old, self.new, 1)
        assert tampered != text, (
            f"tamper drill did not apply; the pinned text moved: {self.old!r}"
        )
        return tampered


@dataclass(frozen=True)
class InjectedRead:
    """A hand-written read injected straight after the ``.inc`` include."""

    key: str
    snippet: str


@dataclass(frozen=True)
class TuningTampers:
    """Per-bundle coordinates for the shared tamper operators.

    Every operator is "same drill, different landmark": the drill bodies live
    once in the gate module, the landmarks live here so each bundle keeps
    tampering a key it actually owns (a middle key for the residue scan, a
    real declared member for the addition drills, and so on).
    """

    default_token_drift: TextTamper  # applied to the .inc
    struct_initializer_drift: TextTamper  # applied to the header
    deleted_inc_key: str  # dropped from the .inc line-wise
    synchronized_rename: TextTamper  # applied to the .inc
    renamed_from: str
    renamed_to: str
    type_drift: TextTamper  # applied to the .inc
    absence_set_leak: TextTamper  # applied to the .inc
    struct_member_addition: TextTamper  # applied to the header
    scalar_read_injection: InjectedRead
    non_value_read_injection: InjectedRead
    # Vector-shaped drills only exist for a bundle whose struct has vectors.
    vector_read_injection: "InjectedRead | None" = None
    struct_vector_member_addition: "TextTamper | None" = None


@dataclass(frozen=True)
class TuningBundleSpec:
    """Everything that differs between two otherwise identical tuning gates."""

    label: str
    struct_name: str
    inc_path: Path
    header_path: Path
    loader_path: Path
    struct_open: str
    member_re: object
    helper_signature: str
    include_directive: str
    scalar_macro: str
    allowed_types: frozenset
    allowed_types_reason: str
    absent_members: tuple
    held_read: str
    held_read_reason: str
    pinned_fields: tuple
    expected_passes: int
    expected_passes_reason: str
    residue_access_prefix: str
    anchor_notes: str
    rationale: str
    tampers: TuningTampers
    vector_macro: "str | None" = None
    vector_cpp_type: "str | None" = None
    expected_vector_fields: "tuple | None" = None
    pinned_order_is_declaration_order: bool = False

    def __post_init__(self) -> None:
        # Guard the parameterisation's one real hazard: a bundle folded into
        # the shared spec while its adjudication text is left behind in a
        # deleted docstring. A one-line "enabled is held" would lose the
        # codec-escape-hatch reasoning that makes the absence reviewable at
        # all, and nothing else in the suite would notice.
        rationale = self.rationale.strip()
        assert rationale, f"{self.label}: absence-set rationale is empty"
        assert len(rationale) > MIN_RATIONALE_CHARS, (
            f"{self.label}: absence-set rationale is {len(rationale)} characters; "
            f"it must carry the adjudication (> {MIN_RATIONALE_CHARS}), not a label"
        )
        assert self.anchor_notes.strip(), f"{self.label}: anchor notes are empty"
        assert self.allowed_types_reason.strip(), f"{self.label}: type contract unexplained"
        assert self.expected_passes_reason.strip(), f"{self.label}: pass contract unexplained"
        assert self.held_read_reason.strip(), f"{self.label}: held read unexplained"

    # -- derived shape ----------------------------------------------------

    @property
    def helper_name(self) -> str:
        return self.helper_signature.split()[-1].rstrip("(")

    @property
    def macros(self) -> frozenset:
        names = {self.scalar_macro}
        if self.vector_macro is not None:
            names.add(self.vector_macro)
        return frozenset(names)

    @property
    def expected_field_count(self) -> int:
        return len(self.pinned_fields)

    def keys(self) -> list:
        return [name for name, _cpp_type, _group in self.pinned_fields]

    def expected_group_for(self, cpp_type: str) -> str:
        """Which macro family a declared member must be listed under. A bundle
        without a vector macro has exactly one family, so the mapping collapses
        to the scalar macro."""
        if self.vector_macro is not None and cpp_type == self.vector_cpp_type:
            return self.vector_macro
        return self.scalar_macro

    # -- readers ----------------------------------------------------------

    @property
    def header_anchor(self) -> WorktreeAnchor:
        """The struct declaration is this bundle's authoritative anchor, and it
        lives in the working tree -- unlike the survey-anchored bundles, whose
        anchor is an immutable git object. Both go through the same anchor
        interface so the difference is a spec choice, not a code path."""
        return WorktreeAnchor(self.header_path)

    def inc_text(self) -> str:
        return self.inc_path.read_text(encoding="utf-8")

    def header_text(self) -> str:
        return self.header_anchor.read_text()

    def loader_text(self) -> str:
        return self.loader_path.read_text(encoding="utf-8")

    def inc_fields(self, inc_text=None):
        return parse_inc_fields(
            self.inc_text() if inc_text is None else inc_text, self.macros
        )

    def struct_members_with_init(self, header_text=None) -> tuple:
        return struct_members_line_scan(
            self.header_text() if header_text is None else header_text,
            struct_open=self.struct_open,
            struct_name=self.struct_name,
            member_re=self.member_re,
            source_label=self.header_anchor.label,
        )

    def struct_members(self, header_text=None) -> tuple:
        return tuple(
            (name, cpp_type)
            for name, cpp_type, _init in self.struct_members_with_init(header_text)
        )

    def helper_body(self, loader_text=None) -> str:
        return function_body(
            self.loader_text() if loader_text is None else loader_text,
            self.helper_signature,
            label=self.helper_name,
        )

    def include_passes(self, loader_text=None) -> int:
        return self.helper_body(loader_text).count(self.include_directive)


# ---------------------------------------------------------------------------
# Checkers. Negative tests drive these with tampered in-memory inputs, so none
# of them may read global state beyond their arguments (the spec included --
# it only carries pinned literals and paths, never file contents).
# ---------------------------------------------------------------------------


def check_member_types_allowed(spec: TuningBundleSpec, struct_members) -> None:
    """The macro/pass shape of a bundle is an adjudicated contract, not an
    accident: a member whose type falls outside the adjudicated set must force
    a re-adjudication instead of silently joining the list."""
    for name, cpp_type in struct_members:
        assert cpp_type in spec.allowed_types, (
            f"{spec.struct_name} member {name} has type {cpp_type}; "
            f"{spec.allowed_types_reason}"
        )


def check_inc_matches_struct(spec: TuningBundleSpec, inc_fields, struct_members) -> None:
    """Anchor assertion: the ``.inc`` covers exactly the declaration's members
    minus the adjudicated absence set, with matching C++ types and macro
    groups."""
    declared = {name: cpp_type for name, cpp_type in struct_members}
    assert len(declared) == len(struct_members), f"duplicate {spec.struct_name} member"

    absent = set(spec.absent_members)
    for member in spec.absent_members:
        assert member in declared, (
            f"absence-set member {member} no longer exists on {spec.struct_name}; "
            "the adjudication must be revisited"
        )

    expected_covered = {name for name in declared if name not in absent}
    inc_names = [field.name for field in inc_fields]
    assert len(set(inc_names)) == len(inc_names), ".inc has a duplicate key"
    assert set(inc_names) == expected_covered, (
        f"{spec.inc_path.name} drifted from the {spec.struct_name} declaration: "
        f"missing={sorted(expected_covered - set(inc_names))} "
        f"unexpected={sorted(set(inc_names) - expected_covered)}"
    )
    for field in inc_fields:
        assert field.cpp_type == declared[field.name], (
            f"{field.name}: .inc type {field.cpp_type} != declared "
            f"{declared[field.name]}"
        )
        expected_group = spec.expected_group_for(declared[field.name])
        assert field.group == expected_group, (
            f"{field.name}: wrong macro group {field.group}"
        )


def check_pinned_matches_struct(spec: TuningBundleSpec, struct_members) -> None:
    """Third leg: the pinned table must itself agree with the declaration on
    the member set and per-member type/group. Order is only cross-checked for
    a bundle whose read order *is* the declaration order; where the two differ
    the pinned table records read order on purpose (see ``anchor_notes``)."""
    declared = dict(struct_members)
    pinned = {name: (cpp_type, group) for name, cpp_type, group in spec.pinned_fields}
    absent = set(spec.absent_members)
    expected_covered = {name for name in declared if name not in absent}
    assert set(pinned) == expected_covered, (
        f"pinned table drifted from the {spec.struct_name} declaration"
    )
    for name, (cpp_type, group) in pinned.items():
        assert cpp_type == declared[name], f"pinned {name}: type disagrees"
        assert group == spec.expected_group_for(declared[name]), (
            f"pinned {name}: wrong macro group"
        )
    if spec.pinned_order_is_declaration_order:
        declaration_order = [
            name for name, _cpp_type in struct_members if name not in absent
        ]
        assert declaration_order == [name for name, _t, _g in spec.pinned_fields], (
            f"pinned order no longer matches the {spec.struct_name} declaration "
            "order (which is also the historical read order for this struct)"
        )


def check_recorded_defaults_match_struct(
    spec: TuningBundleSpec, inc_fields, struct_members_with_init
) -> None:
    """The ``.inc``'s default_value token is parity-only (the parse never
    expands it), so nothing in the build would notice if it drifted from the
    struct initializer it claims to mirror. This check is what makes that
    claim load-bearing: every scalar row's recorded token must equal the
    declared initializer verbatim, and every vector row must record ``{}`` for
    the default-constructed empty table."""
    declared_init = {name: init for name, _cpp_type, init in struct_members_with_init}
    for field in inc_fields:
        recorded = field.default.strip()
        if spec.vector_macro is not None and field.group == spec.vector_macro:
            assert declared_init[field.name] == "", (
                f"{field.name}: declared vector gained an initializer "
                f"({declared_init[field.name]!r}); the .inc records `{{}}`"
            )
            assert recorded == "{}", (
                f"{field.name}: vector rows must record `{{}}`, got {recorded!r}"
            )
            continue
        assert recorded == declared_init[field.name], (
            f"{field.name}: .inc records default {recorded!r} but "
            f"{spec.struct_name} declares {declared_init[field.name]!r}; the "
            "parity-only token must mirror the struct initializer exactly"
        )
