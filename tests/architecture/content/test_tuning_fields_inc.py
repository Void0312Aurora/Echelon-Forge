"""Anti-drift gate for the flight-dynamics tuning parse field lists.

Two bundles share this module because they are the same gate twice over:

- **AeroTuning** (T11 slice 4 bundle 3, I66): the 44 purely-mechanical JSON
  keys read by ``parse_aero_tuning_json_fields``, single-sourced at
  ``src/content/detail/aero_tuning_fields.inc``.
- **EngineTuning** (the iteration after it): the 16 purely-mechanical JSON
  keys read by ``parse_engine_tuning_json_fields``, single-sourced at
  ``src/content/detail/engine_tuning_fields.inc``.

Both follow the I58 ``missile_tuning_fields.inc`` precedent and the landed I61
direct-fields test template, and both parse the *same* header
(``flight_dynamics_tuning.h``) and the *same* loader
(``unit_definition_loader.cpp``).

Shared anchor structure (the I58 review-hardening discipline: the gate must
not be a two-way comparison that a synchronized tamper can satisfy):

- The **struct declaration** is parsed at test time and is the authoritative
  anchor. For neither bundle does the I52 survey carry a per-key table -- it
  records ``aero_tuning`` and ``engine_tuning`` as single object rows -- so
  the declaration is the only independent inventory of these parse surfaces.
  The ``.inc`` must cover exactly the declaration's members minus the
  adjudicated absence set, with matching C++ types and macro groups.
- The pinned ``pinned_fields`` table in each spec is a third leg of a
  three-way cross-check (declaration == .inc == pinned), so a
  header-edit-plus-.inc-edit still needs a matching edit here to pass.
- The helper body is located by text boundary (signature + brace matching)
  and scanned for hand-written read residues of **every** migrated key, plus
  a stricter no-quoted-key-literal belt, so a re-introduced hand-written read
  of any key -- first, middle, or last -- goes red.
- The include-pass contract is pinned per bundle, because it is what makes
  the expansion token-for-token equal to the pre-change statement order.

Everything that differs between the two lives in a ``TuningBundleSpec``, and
the per-bundle adjudication text lives in that spec's ``rationale`` /
``anchor_notes`` / ``*_reason`` fields rather than in prose here, so it cannot
drift away from the bundle it justifies.
"""

from __future__ import annotations

import re

import pytest

from tests.support.paths import REPO_ROOT
from tests.support.tuning_inc_gate import (
    MIN_RATIONALE_CHARS,
    InjectedRead,
    TextTamper,
    TuningBundleSpec,
    TuningTampers,
    check_inc_matches_struct,
    check_member_types_allowed,
    check_pinned_matches_struct,
    check_recorded_defaults_match_struct,
)
from tests.support.xmacro_gate import quoted_key_literals, read_residues


# Both tuning structs are declared in one header and parsed by one loader.
_HEADER_PATH = (
    REPO_ROOT
    / "src"
    / "components"
    / "domains"
    / "air"
    / "platform"
    / "flight_dynamics_tuning.h"
)
_LOADER_PATH = REPO_ROOT / "src" / "content" / "unit_definition_loader.cpp"
_DETAIL_DIR = REPO_ROOT / "src" / "content" / "detail"

_AERO_SCALAR_MACRO = "EF_AERO_TUNING_FIELD"
_AERO_VECTOR_MACRO = "EF_AERO_TUNING_VECTOR_FIELD"
_ENGINE_SCALAR_MACRO = "EF_ENGINE_TUNING_FIELD"
_VECTOR_CPP_TYPE = "std::vector<double>"

# The hand-written literal-default read held back by both adjudications. The
# line is byte-identical in the two helpers, which is exactly why the removal
# drill below has to be body-scoped.
_ENABLED_HAND_WRITTEN_READ = 'tuning.enabled = src.value("enabled", true);'

# Declaration parsing. Members are plain `<type> <name> = <init>;` lines, or
# bare `std::vector<double> <name>;` for the default-constructed mach tables.
# std::vector<double> stays in the alternation even for the scalars-only
# EngineTuning bundle so a future vector member there is *parsed* and then
# rejected by that bundle's type gate (single-macro adjudication) instead of
# being silently skipped.
_MEMBER_RE = re.compile(
    r"^(?P<type>bool|double|std::vector<double>)\s+(?P<name>\w+)"
    r"\s*(?:=\s*(?P<init>[^;]*?)\s*)?;$"
)


# ---------------------------------------------------------------------------
# Bundle 1: AeroTuning.
# ---------------------------------------------------------------------------

# Pinned third leg (declaration == .inc == pinned): (member, cpp_type, macro).
# Order is the historical hand-written READ order, which differs from the
# declaration order: the struct declares control_effectiveness_scale_vs_mach
# among the scalars (between fbw_pitch_rate_per_g_err and actuator_tau_*),
# while the hand-written body read all scalars first and all vectors after,
# putting it last. Read order is what token-for-token parity requires, so read
# order is what the .inc pins; the struct layout is untouched (ABI red line).
_AERO_PINNED = (
    ("cl_alpha_per_deg", "double", _AERO_SCALAR_MACRO),
    ("cl0", "double", _AERO_SCALAR_MACRO),
    ("cd0_clean", "double", _AERO_SCALAR_MACRO),
    ("induced_drag_k", "double", _AERO_SCALAR_MACRO),
    ("cm_alpha_per_rad", "double", _AERO_SCALAR_MACRO),
    ("cm_q", "double", _AERO_SCALAR_MACRO),
    ("alpha_stall_clean_deg", "double", _AERO_SCALAR_MACRO),
    ("alpha_stall_flaps_full_deg", "double", _AERO_SCALAR_MACRO),
    ("alpha_peak_offset_deg", "double", _AERO_SCALAR_MACRO),
    ("alpha_deep_offset_deg", "double", _AERO_SCALAR_MACRO),
    ("cl_peak_clean", "double", _AERO_SCALAR_MACRO),
    ("cl_peak_flaps_full", "double", _AERO_SCALAR_MACRO),
    ("cl_deep_clean", "double", _AERO_SCALAR_MACRO),
    ("cl_deep_flaps_full", "double", _AERO_SCALAR_MACRO),
    ("pitch_break_onset_deg", "double", _AERO_SCALAR_MACRO),
    ("pitch_break_full_deg", "double", _AERO_SCALAR_MACRO),
    ("pitch_break_cm_nose_down", "double", _AERO_SCALAR_MACRO),
    ("post_stall_damp_floor", "double", _AERO_SCALAR_MACRO),
    ("aoa_rate_pitch_break_gain", "double", _AERO_SCALAR_MACRO),
    ("elevator_max_deflection_deg", "double", _AERO_SCALAR_MACRO),
    ("aileron_max_deflection_deg", "double", _AERO_SCALAR_MACRO),
    ("rudder_max_deflection_deg", "double", _AERO_SCALAR_MACRO),
    ("cm_delta_e_per_rad", "double", _AERO_SCALAR_MACRO),
    ("cl_delta_a_per_rad", "double", _AERO_SCALAR_MACRO),
    ("cn_delta_r_per_rad", "double", _AERO_SCALAR_MACRO),
    ("fbw_elevator_cmd_per_rate_err", "double", _AERO_SCALAR_MACRO),
    ("fbw_aileron_cmd_per_rate_err", "double", _AERO_SCALAR_MACRO),
    ("fbw_rudder_cmd_per_rate_err", "double", _AERO_SCALAR_MACRO),
    ("ari_rudder_cmd_per_aileron_cmd", "double", _AERO_SCALAR_MACRO),
    ("fbw_g_command_enabled", "bool", _AERO_SCALAR_MACRO),
    ("fbw_g_command_neutral", "double", _AERO_SCALAR_MACRO),
    ("fbw_g_command_max", "double", _AERO_SCALAR_MACRO),
    ("fbw_g_command_min", "double", _AERO_SCALAR_MACRO),
    ("fbw_pitch_rate_per_g_err", "double", _AERO_SCALAR_MACRO),
    ("actuator_tau_elevator_s", "double", _AERO_SCALAR_MACRO),
    ("actuator_tau_aileron_s", "double", _AERO_SCALAR_MACRO),
    ("actuator_tau_rudder_s", "double", _AERO_SCALAR_MACRO),
    ("mach_breakpoints", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("cl_alpha_scale_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("cd0_add_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("induced_drag_scale_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("cm_alpha_scale_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("stall_alpha_delta_deg_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
    ("control_effectiveness_scale_vs_mach", _VECTOR_CPP_TYPE, _AERO_VECTOR_MACRO),
)

AERO = TuningBundleSpec(
    label="aero",
    struct_name="AeroTuning",
    inc_path=_DETAIL_DIR / "aero_tuning_fields.inc",
    header_path=_HEADER_PATH,
    loader_path=_LOADER_PATH,
    struct_open="struct AeroTuning {",
    member_re=_MEMBER_RE,
    helper_signature="void parse_aero_tuning_json_fields(",
    include_directive='#include "content/detail/aero_tuning_fields.inc"',
    scalar_macro=_AERO_SCALAR_MACRO,
    vector_macro=_AERO_VECTOR_MACRO,
    vector_cpp_type=_VECTOR_CPP_TYPE,
    allowed_types=frozenset({"bool", "double", _VECTOR_CPP_TYPE}),
    allowed_types_reason=(
        "the aero_tuning_fields.inc contract covers bool/double scalars and "
        "std::vector<double> mach tables; any other member type must be "
        "re-adjudicated before it is parsed"
    ),
    absent_members=("enabled",),
    held_read=_ENABLED_HAND_WRITTEN_READ,
    held_read_reason=(
        "the hand-written literal-default read of `enabled` must survive: the "
        "airframe.tuning / aero_tuning preset-then-merge path depends on it"
    ),
    pinned_fields=_AERO_PINNED,
    expected_vector_fields=(
        "mach_breakpoints",
        "cl_alpha_scale_vs_mach",
        "cd0_add_vs_mach",
        "induced_drag_scale_vs_mach",
        "cm_alpha_scale_vs_mach",
        "stall_alpha_delta_deg_vs_mach",
        "control_effectiveness_scale_vs_mach",
    ),
    expected_passes=2,
    expected_passes_reason=(
        "parse_aero_tuning_json_fields must include the single-source list "
        "twice (scalars before the parse_vector lambda, vectors after) to "
        "preserve the pre-change statement order"
    ),
    pinned_order_is_declaration_order=False,
    residue_access_prefix=r"(?:src\s*\.\s*value|parse_vector)\s*\(\s*",
    anchor_notes=(
        "Unlike the missile-tuning bundle (whose anchor is the I52 survey's "
        "explicit 52-row table), the I52 survey has no per-key table for the "
        "aero helper -- it records `aero_tuning` as a single object row "
        "(section 1.1 row 29) -- so the struct declaration is the only "
        "independent inventory of this parse surface. The pinned order is the "
        "historical READ order, which differs from the declaration order: the "
        "struct declares control_effectiveness_scale_vs_mach among the scalars "
        "while the hand-written body read all scalars first and all vectors "
        "after. Read order is what token-for-token parity requires, so read "
        "order is what the .inc pins; the struct layout is untouched (ABI red "
        "line). The two-pass include contract is what reproduces that order."
    ),
    rationale=(
        "ABSENCE SET: `enabled` is the one member read by the helper that "
        "stays hand-written. Its read takes a *literal* `true` default rather "
        "than the \"missing key keeps the existing value\" form, which is "
        "load-bearing for the `airframe.tuning` / `aero_tuning` codec escape "
        "hatch (census section 3 red line \"codec escape hatches must be "
        "preserved\"): both call sites seed from the "
        "`flight_dynamics::default_aero_tuning()` preset and then merge, so a "
        "present `aero_tuning` object without an `enabled` key must still come "
        "out enabled. This gate pins both that `enabled` is absent from the "
        "`.inc` and that the literal-default hand-written read is still "
        "present in the helper body."
    ),
    tampers=TuningTampers(
        default_token_drift=TextTamper(
            "EF_AERO_TUNING_FIELD(double, cm_q, -12.0)",
            "EF_AERO_TUNING_FIELD(double, cm_q, -13.0)",
        ),
        struct_initializer_drift=TextTamper(
            "double cm_q = -12.0;", "double cm_q = -14.0;"
        ),
        deleted_inc_key="actuator_tau_rudder_s",
        synchronized_rename=TextTamper(
            "EF_AERO_TUNING_FIELD(double, cm_q,",
            "EF_AERO_TUNING_FIELD(double, cm_qq,",
        ),
        renamed_from="cm_q",
        renamed_to="cm_qq",
        type_drift=TextTamper(
            "EF_AERO_TUNING_FIELD(bool, fbw_g_command_enabled,",
            "EF_AERO_TUNING_FIELD(double, fbw_g_command_enabled,",
        ),
        absence_set_leak=TextTamper(
            "EF_AERO_TUNING_FIELD(double, cl_alpha_per_deg, 0.1)",
            "EF_AERO_TUNING_FIELD(bool, enabled, false)\n"
            "EF_AERO_TUNING_FIELD(double, cl_alpha_per_deg, 0.1)",
        ),
        struct_member_addition=TextTamper(
            "    double actuator_tau_rudder_s = 0.12;",
            "    double actuator_tau_rudder_s = 0.12;\n    double brand_new_knob = 1.0;",
        ),
        scalar_read_injection=InjectedRead(
            key="cm_q",
            snippet='    tuning.cm_q = src.value("cm_q", tuning.cm_q);\n',
        ),
        vector_read_injection=InjectedRead(
            key="mach_breakpoints",
            snippet='    parse_vector("mach_breakpoints", &tuning.mach_breakpoints);\n',
        ),
        non_value_read_injection=InjectedRead(
            key="cd0_clean",
            snippet=(
                '    if (src.contains("cd0_clean")) {\n'
                '        tuning.cd0_clean = src["cd0_clean"].get<double>();\n'
                "    }\n"
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Bundle 2: EngineTuning.
# ---------------------------------------------------------------------------

# Pinned third leg. Order is both the declaration order and the historical
# hand-written read order, which for this struct are identical (unlike
# AeroTuning), so the order cross-check is enabled for this bundle.
_ENGINE_PINNED = (
    ("mil_thrust_n", "double", _ENGINE_SCALAR_MACRO),
    ("ab_thrust_n", "double", _ENGINE_SCALAR_MACRO),
    ("throttle_ab_threshold", "double", _ENGINE_SCALAR_MACRO),
    ("throttle_idle_bias", "double", _ENGINE_SCALAR_MACRO),
    ("tau_spool_up_s", "double", _ENGINE_SCALAR_MACRO),
    ("tau_spool_down_s", "double", _ENGINE_SCALAR_MACRO),
    ("tau_ab_light_s", "double", _ENGINE_SCALAR_MACRO),
    ("tau_ab_extinguish_s", "double", _ENGINE_SCALAR_MACRO),
    ("ram_rise_gain", "double", _ENGINE_SCALAR_MACRO),
    ("ram_rise_mach_cap", "double", _ENGINE_SCALAR_MACRO),
    ("ram_decay_start_mach", "double", _ENGINE_SCALAR_MACRO),
    ("ram_decay_gain", "double", _ENGINE_SCALAR_MACRO),
    ("thrust_sigma_exponent", "double", _ENGINE_SCALAR_MACRO),
    ("thrust_theta_exponent", "double", _ENGINE_SCALAR_MACRO),
    ("tsfc_mil_kg_per_nh", "double", _ENGINE_SCALAR_MACRO),
    ("tsfc_ab_kg_per_nh", "double", _ENGINE_SCALAR_MACRO),
)

ENGINE = TuningBundleSpec(
    label="engine",
    struct_name="EngineTuning",
    inc_path=_DETAIL_DIR / "engine_tuning_fields.inc",
    header_path=_HEADER_PATH,
    loader_path=_LOADER_PATH,
    struct_open="struct EngineTuning {",
    member_re=_MEMBER_RE,
    helper_signature="void parse_engine_tuning_json_fields(",
    include_directive='#include "content/detail/engine_tuning_fields.inc"',
    scalar_macro=_ENGINE_SCALAR_MACRO,
    allowed_types=frozenset({"bool", "double"}),
    allowed_types_reason=(
        "the single-macro engine_tuning_fields.inc contract covers only "
        "bool/double scalars and must be re-adjudicated before this member is "
        "parsed"
    ),
    absent_members=("enabled",),
    held_read=_ENABLED_HAND_WRITTEN_READ,
    held_read_reason=(
        "the hand-written literal-default read of `enabled` must survive: the "
        "engine.tuning / engine_tuning preset-then-merge path depends on it"
    ),
    pinned_fields=_ENGINE_PINNED,
    expected_passes=1,
    expected_passes_reason=(
        "parse_engine_tuning_json_fields must include the single-source list "
        "exactly once: EngineTuning has no vector members, so there is no "
        "second (vector) pass, and zero passes drops all 16 reads"
    ),
    pinned_order_is_declaration_order=True,
    residue_access_prefix=r"src\s*\.\s*value\s*\(\s*",
    anchor_notes=(
        "As with the aero bundle, the I52 survey has no per-key table for the "
        "engine helper -- it records `engine_tuning` as a single object row -- "
        "so the struct declaration is the only independent inventory of this "
        "parse surface. The SINGLE-pass include contract is pinned (exactly "
        "one include of the list inside the helper): unlike the aero helper "
        "there is no parse_vector lambda to order around, because EngineTuning "
        "has no vector members. The gate also pins that member-type set, so a "
        "future vector member forces the adjudication and pass structure to be "
        "revisited rather than silently extended."
    ),
    rationale=(
        "ABSENCE SET: `enabled` is the one member read by the helper that "
        "stays hand-written. Its read takes a *literal* `true` default rather "
        "than the \"missing key keeps the existing value\" form, which is "
        "load-bearing for the `engine.tuning` / `engine_tuning` codec escape "
        "hatch (census red line \"codec escape hatches must be preserved\"): "
        "both call sites seed from the "
        "`flight_dynamics::default_engine_tuning()` preset and then merge, so "
        "a present tuning object without an `enabled` key must still come out "
        "enabled. The top-level `engine_tuning` call site additionally "
        "branches on `tuning.enabled` to decide whether to re-seed before "
        "merging on top of an `engine.tuning` block. This gate pins both that "
        "`enabled` is absent from the `.inc` and that the literal-default "
        "hand-written read is still present in the helper body."
    ),
    tampers=TuningTampers(
        default_token_drift=TextTamper(
            "EF_ENGINE_TUNING_FIELD(double, tau_spool_up_s, 2.5)",
            "EF_ENGINE_TUNING_FIELD(double, tau_spool_up_s, 9.9)",
        ),
        struct_initializer_drift=TextTamper(
            "double tau_spool_up_s = 2.5;", "double tau_spool_up_s = 3.5;"
        ),
        deleted_inc_key="tsfc_ab_kg_per_nh",
        synchronized_rename=TextTamper(
            "EF_ENGINE_TUNING_FIELD(double, ram_rise_gain,",
            "EF_ENGINE_TUNING_FIELD(double, ram_rise_gainn,",
        ),
        renamed_from="ram_rise_gain",
        renamed_to="ram_rise_gainn",
        type_drift=TextTamper(
            "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n,",
            "EF_ENGINE_TUNING_FIELD(bool, mil_thrust_n,",
        ),
        absence_set_leak=TextTamper(
            "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n, 0.0)",
            "EF_ENGINE_TUNING_FIELD(bool, enabled, false)\n"
            "EF_ENGINE_TUNING_FIELD(double, mil_thrust_n, 0.0)",
        ),
        struct_member_addition=TextTamper(
            "    double tsfc_ab_kg_per_nh = 0.25;",
            "    double tsfc_ab_kg_per_nh = 0.25;\n    double brand_new_knob = 1.0;",
        ),
        struct_vector_member_addition=TextTamper(
            "    double tsfc_ab_kg_per_nh = 0.25;",
            "    double tsfc_ab_kg_per_nh = 0.25;\n"
            "    std::vector<double> thrust_scale_vs_mach;",
        ),
        scalar_read_injection=InjectedRead(
            key="ram_rise_gain",
            snippet=(
                '    tuning.ram_rise_gain = src.value("ram_rise_gain", '
                "tuning.ram_rise_gain);\n"
            ),
        ),
        non_value_read_injection=InjectedRead(
            key="ab_thrust_n",
            snippet=(
                '    if (src.contains("ab_thrust_n")) {\n'
                '        tuning.ab_thrust_n = src["ab_thrust_n"].get<double>();\n'
                "    }\n"
            ),
        ),
    ),
)


BUNDLES = (AERO, ENGINE)


def _ids(specs) -> list:
    return [spec.label for spec in specs]


def _subset(predicate) -> list:
    return [spec for spec in BUNDLES if predicate(spec)]


_VECTOR_LIST_BUNDLES = _subset(lambda spec: spec.expected_vector_fields is not None)
_VECTOR_INJECTION_BUNDLES = _subset(
    lambda spec: spec.tampers.vector_read_injection is not None
)
_TYPE_GATE_DRILL_BUNDLES = _subset(
    lambda spec: spec.tampers.struct_vector_member_addition is not None
)

over_bundles = pytest.mark.parametrize("spec", BUNDLES, ids=_ids(BUNDLES))


def _inject_after_include(spec: TuningBundleSpec, snippet: str) -> str:
    marker = spec.include_directive + "\n"
    return TextTamper(marker, marker + snippet).apply(spec.loader_text())


# ---------------------------------------------------------------------------
# Positive gates.
# ---------------------------------------------------------------------------


@over_bundles
def test_inc_exists_and_parses(spec: TuningBundleSpec) -> None:
    assert spec.inc_path.is_file(), f"missing single-source field list: {spec.inc_path}"
    assert len(spec.inc_fields()) == spec.expected_field_count


@over_bundles
def test_struct_declaration_parses(spec: TuningBundleSpec) -> None:
    members = spec.struct_members()
    # Migrated keys + the held absence-set members.
    assert len(members) == spec.expected_field_count + len(spec.absent_members)
    check_member_types_allowed(spec, members)


@over_bundles
def test_inc_matches_struct_declaration_anchor(spec: TuningBundleSpec) -> None:
    check_inc_matches_struct(spec, spec.inc_fields(), spec.struct_members())


@over_bundles
def test_pinned_table_matches_struct_third_leg(spec: TuningBundleSpec) -> None:
    check_pinned_matches_struct(spec, spec.struct_members())


@over_bundles
def test_recorded_defaults_mirror_the_struct_initializers(spec: TuningBundleSpec) -> None:
    # The default_value token is parity-only (the parse never expands it), so
    # without this gate it could drift from the initializer it claims to
    # mirror and nothing in the build would notice.
    check_recorded_defaults_match_struct(
        spec, spec.inc_fields(), spec.struct_members_with_init()
    )


@over_bundles
def test_inc_order_is_the_pinned_read_order(spec: TuningBundleSpec) -> None:
    # Read order is what token-for-token parity with the pre-change body
    # requires. For EngineTuning it coincides with declaration order; for
    # AeroTuning it deliberately does not (see the spec's anchor_notes and the
    # .inc header).
    inc_fields = spec.inc_fields()
    assert [field.name for field in inc_fields] == spec.keys()
    if spec.vector_macro is None:
        return
    groups = [field.group for field in inc_fields]
    assert groups == sorted(groups, key=lambda g: 0 if g == spec.scalar_macro else 1), (
        "the .inc must list all scalar rows before all vector rows: the "
        "loader's two-pass include reproduces the pre-change statement order "
        "from it"
    )


@pytest.mark.parametrize("spec", _VECTOR_LIST_BUNDLES, ids=_ids(_VECTOR_LIST_BUNDLES))
def test_vector_family_is_exactly_the_pinned_mach_tables(spec: TuningBundleSpec) -> None:
    vectors = tuple(
        field.name for field in spec.inc_fields() if field.group == spec.vector_macro
    )
    assert vectors == spec.expected_vector_fields


@over_bundles
def test_no_angle_bracket_comma_type_entered_the_list(spec: TuningBundleSpec) -> None:
    # Census red line "X-macro comma blockers" / I31 precedent: the
    # preprocessor pairs only parentheses, so a type carrying an intra-angle
    # comma would be mis-split. No member of either struct qualifies and no
    # alias exemption is used, so every row's recorded type must be comma-free.
    for field in spec.inc_fields():
        assert "," not in field.cpp_type, (
            f"{field.name}: angle-bracket-comma type {field.cpp_type} must be "
            "held hand-written per the I31 precedent, not aliased into the list"
        )
    for _name, cpp_type in spec.struct_members():
        assert "," not in cpp_type, (
            f"{spec.struct_name} gained an angle-bracket-comma member "
            f"({cpp_type}); it must be adjudicated before entering the X-macro list"
        )


@over_bundles
def test_absence_set_is_absent_and_its_hand_written_read_survives(
    spec: TuningBundleSpec,
) -> None:
    inc_names = {field.name for field in spec.inc_fields()}
    body = spec.helper_body()
    for member in spec.absent_members:
        assert member not in inc_names, (
            f"{member} is not a mechanical read and must stay hand-written"
        )
    # The literal `true` default is the codec escape hatch's contract.
    assert spec.held_read in body, spec.held_read_reason


@over_bundles
def test_absence_set_rationale_is_recorded(spec: TuningBundleSpec) -> None:
    # The parameterisation's own failure mode: a spec that keeps the key list
    # but drops the adjudication text that makes the absence reviewable. The
    # spec's __post_init__ already refuses to construct without it; this gate
    # states it as a named, reported check rather than an import-time crash.
    rationale = spec.rationale.strip()
    assert rationale, f"{spec.label}: absence-set rationale is empty"
    assert len(rationale) > MIN_RATIONALE_CHARS, (
        f"{spec.label}: absence-set rationale is only {len(rationale)} characters"
    )
    for member in spec.absent_members:
        assert member in rationale, (
            f"{spec.label}: the rationale must name the held member {member}"
        )


@over_bundles
def test_loader_helper_consumes_the_inc_in_the_pinned_passes(
    spec: TuningBundleSpec,
) -> None:
    assert spec.include_passes() == spec.expected_passes, spec.expected_passes_reason


@over_bundles
def test_helper_body_has_no_hand_written_read_for_any_migrated_key(
    spec: TuningBundleSpec,
) -> None:
    body = spec.helper_body()
    keys = spec.keys()
    assert read_residues(body, keys, spec.residue_access_prefix) == []
    assert quoted_key_literals(body, keys) == []


# ---------------------------------------------------------------------------
# Negative gates (in-memory tamper drills; the gate must go red).
# ---------------------------------------------------------------------------


@over_bundles
def test_default_token_drift_goes_red(spec: TuningBundleSpec) -> None:
    # The drill that found this gap during authoring: silently changing a
    # recorded default must not stay green.
    tampered = spec.tampers.default_token_drift.apply(spec.inc_text())
    with pytest.raises(AssertionError):
        check_recorded_defaults_match_struct(
            spec, spec.inc_fields(tampered), spec.struct_members_with_init()
        )


@over_bundles
def test_struct_initializer_drift_goes_red(spec: TuningBundleSpec) -> None:
    # The other direction: retuning the struct default without updating the
    # .inc must also trip the parity gate.
    tampered = spec.tampers.struct_initializer_drift.apply(spec.header_text())
    with pytest.raises(AssertionError):
        check_recorded_defaults_match_struct(
            spec, spec.inc_fields(), spec.struct_members_with_init(tampered)
        )


@over_bundles
def test_key_deletion_from_inc_goes_red_against_struct(spec: TuningBundleSpec) -> None:
    key = spec.tampers.deleted_inc_key
    dropped = "".join(
        line for line in spec.inc_text().splitlines(keepends=True) if key not in line
    )
    mutated = spec.inc_fields(dropped)
    assert len(mutated) == spec.expected_field_count - 1
    with pytest.raises(AssertionError):
        check_inc_matches_struct(spec, mutated, spec.struct_members())


@over_bundles
def test_struct_anchor_catches_synchronized_inc_and_pinned_tamper(
    spec: TuningBundleSpec,
) -> None:
    # A tamper of the .inc AND the pinned table the same way would satisfy a
    # two-way gate. The struct declaration is untampered, so the gate goes red.
    tampered_inc_text = spec.tampers.synchronized_rename.apply(spec.inc_text())
    tampered_fields = spec.inc_fields(tampered_inc_text)
    renamed_from = spec.tampers.renamed_from
    renamed_to = spec.tampers.renamed_to
    tampered_pinned = tuple(
        (renamed_to if name == renamed_from else name, cpp_type, group)
        for name, cpp_type, group in spec.pinned_fields
    )

    # Old-style two-way comparison stays green after the synchronized tamper.
    assert [field.name for field in tampered_fields] == [
        name for name, _cpp_type, _group in tampered_pinned
    ]

    # Struct anchor catches it.
    with pytest.raises(AssertionError):
        check_inc_matches_struct(spec, tampered_fields, spec.struct_members())


@over_bundles
def test_type_drift_in_inc_goes_red(spec: TuningBundleSpec) -> None:
    tampered = spec.tampers.type_drift.apply(spec.inc_text())
    with pytest.raises(AssertionError):
        check_inc_matches_struct(spec, spec.inc_fields(tampered), spec.struct_members())


@over_bundles
def test_absence_set_leak_goes_red(spec: TuningBundleSpec) -> None:
    # Folding a held member into the list would silently change its literal
    # default into the seeded value and break the codec escape hatch (and, for
    # the engine bundle, the top-level call site's re-seed branch). See the
    # spec rationale.
    leaked = spec.tampers.absence_set_leak.apply(spec.inc_text())
    with pytest.raises(AssertionError):
        check_inc_matches_struct(spec, spec.inc_fields(leaked), spec.struct_members())


@over_bundles
def test_struct_member_addition_goes_red(spec: TuningBundleSpec) -> None:
    # A new member that the parse map does not cover must trip the gate rather
    # than silently become an unread key.
    tampered = spec.tampers.struct_member_addition.apply(spec.header_text())
    with pytest.raises(AssertionError):
        check_inc_matches_struct(spec, spec.inc_fields(), spec.struct_members(tampered))


@pytest.mark.parametrize(
    "spec", _TYPE_GATE_DRILL_BUNDLES, ids=_ids(_TYPE_GATE_DRILL_BUNDLES)
)
def test_struct_vector_member_addition_trips_the_type_gate(
    spec: TuningBundleSpec,
) -> None:
    # The single-macro / single-pass shape is an adjudicated contract, not an
    # accident: a vector member must force a re-adjudication (macro split,
    # pass structure, parse_vector semantics) instead of silently joining the
    # list.
    tampered = spec.tampers.struct_vector_member_addition.apply(spec.header_text())
    with pytest.raises(AssertionError):
        check_member_types_allowed(spec, spec.struct_members(tampered))


@over_bundles
def test_residue_scan_catches_middle_key_hand_written_injection(
    spec: TuningBundleSpec,
) -> None:
    injection = spec.tampers.scalar_read_injection
    body = spec.helper_body(_inject_after_include(spec, injection.snippet))
    keys = spec.keys()
    assert read_residues(body, keys, spec.residue_access_prefix) == [injection.key]
    assert quoted_key_literals(body, keys) == [injection.key]


@pytest.mark.parametrize(
    "spec", _VECTOR_INJECTION_BUNDLES, ids=_ids(_VECTOR_INJECTION_BUNDLES)
)
def test_residue_scan_catches_vector_key_hand_written_injection(
    spec: TuningBundleSpec,
) -> None:
    injection = spec.tampers.vector_read_injection
    body = spec.helper_body(_inject_after_include(spec, injection.snippet))
    assert read_residues(body, spec.keys(), spec.residue_access_prefix) == [
        injection.key
    ]


@over_bundles
def test_quoted_literal_belt_catches_non_value_form_injection(
    spec: TuningBundleSpec,
) -> None:
    # A hand-written access avoiding the src.value / parse_vector shapes slips
    # past the pattern scan by design; the quoted-literal belt still catches it.
    injection = spec.tampers.non_value_read_injection
    body = spec.helper_body(_inject_after_include(spec, injection.snippet))
    keys = spec.keys()
    assert read_residues(body, keys, spec.residue_access_prefix) == []
    assert quoted_key_literals(body, keys) == [injection.key]


@over_bundles
def test_include_pass_collapse_goes_red(spec: TuningBundleSpec) -> None:
    # Dropping one include pass drops the reads it carried: for the two-pass
    # aero helper that is 37 scalar reads or 7 vector reads, for the
    # single-pass engine helper it is all 16.
    loader = spec.loader_text()
    collapsed = TextTamper(spec.include_directive + "\n", "").apply(loader)
    assert spec.include_passes(collapsed) == spec.expected_passes - 1


@over_bundles
def test_held_read_removal_goes_red(spec: TuningBundleSpec) -> None:
    # Body-scoped on purpose: the identical `enabled` read line exists in BOTH
    # tuning helpers, and the aero helper precedes the engine helper in the
    # file, so a whole-file replace(..., 1) would tamper the wrong function and
    # leave the engine bundle's gate green.
    loader = spec.loader_text()
    body = spec.helper_body(loader)
    assert spec.held_read in body
    stripped_body = body.replace(spec.held_read, "", 1)
    stripped = loader.replace(body, stripped_body, 1)
    assert stripped != loader
    assert spec.held_read not in spec.helper_body(stripped)
