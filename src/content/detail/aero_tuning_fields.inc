// Single-source X-macro field list for AeroTuning's JSON parse (T11 slice 4
// bundle 3 / this iteration). Owns the 44 purely-mechanical keys read by
// parse_aero_tuning_json_fields (content/unit_definition_loader.cpp). This is
// the aero sibling of the I58 missile_tuning_fields.inc precedent and follows
// its scope-adjudication discipline.
//
// SCOPE (the mechanical subset, adjudicated member-by-member against the
// AeroTuning declaration in
// components/domains/air/platform/flight_dynamics_tuning.h): a key lives here
// only if its pre-change read is the exact single-line form
//   scalar:  tuning.<member> = src.value("<member>", tuning.<member>);
//   vector:  parse_vector("<member>", &tuning.<member>);
// with the JSON key byte-identical to the member name and NO escape-hatch /
// object-block / has_*-flag / clamp / fallback coupling.
//
// DELIBERATELY ABSENT -- `enabled`. It is the one AeroTuning member read by the
// helper that is not mechanical: its pre-change read is
//   tuning.enabled = src.value("enabled", true);
// i.e. a *literal* `true` default, not the "missing key keeps the existing
// value" default the other 44 keys use. That literal is load-bearing for the
// airframe.tuning / aero_tuning codec escape hatch (survey section 2, census
// red line "codec escape hatches"): both call sites seed the struct from the
// flight_dynamics::default_aero_tuning() preset and then merge, and a present
// aero_tuning object with no "enabled" key must still come out enabled. Folding
// it into the scalar row shape below would silently change that default from
// `true` to the seeded value, so it stays hand-written directly above the
// include. Absence is pinned by
// tests/architecture/content/test_aero_tuning_fields_inc.py.
//
// ANGLE-BRACKET-COMMA ADJUDICATION (census red line "X-macro comma blockers",
// I31 precedent). Every AeroTuning member was checked: the only templated
// members are the seven std::vector<double> mach/authority tables, which carry
// no intra-angle comma, so nothing is mis-split by the preprocessor and no
// member is held on comma grounds. This matches the I52 survey section 5
// finding for MissileTuningDefinition (`UnitDefinition::default_loadout` remains
// the sole blocker in the two structs it scanned, and it is not an AeroTuning
// member). No type-alias exemption is used anywhere in this list.
//
// Consumers define both macros before including; the footer #undef's them:
//   EF_AERO_TUNING_FIELD(cpp_type, name, default_value)         scalar key
//   EF_AERO_TUNING_VECTOR_FIELD(cpp_type, name, default_value)  std::vector<double> key
// Because the #undef footer clears both, the list is re-includable, and the
// loader deliberately includes it TWICE: once with only the scalar macro
// productive and once with only the vector macro productive. That is what keeps
// the emitted statement order token-identical to the pre-change hand-written
// body, in which the 37 scalar reads preceded the local parse_vector lambda
// declaration and the 7 vector reads followed it. A conforming consumer may
// therefore define either macro as empty; both must still be defined.
//
// DEFAULT_VALUE TOKEN: parity-only, NOT parse-consumed. As in I58 (and unlike
// the I61 unit_definition_direct_fields.inc bundle, landed as commit
// e710d64f on codex/redundancy-consolidation, whose hand-written reads
// used literal defaults), the "missing key keeps the existing value" semantics
// is carried by the parse-side src.value(key, current) / parse_vector expansion,
// so the default_value token recorded here is never expanded into the parse. It
// mirrors the AeroTuning declaration's own initializer for review parity and
// future struct single-sourcing; the vector rows record `{}` for the
// default-constructed empty tables.
//
// FIELD ORDER mirrors the historical hand-written *read* order, which for this
// struct is NOT identical to the declaration order: AeroTuning declares
// control_effectiveness_scale_vs_mach between fbw_pitch_rate_per_g_err and the
// actuator_tau_* scalars, while the hand-written body read all 37 scalars first
// and then the seven vectors, putting control_effectiveness_scale_vs_mach last.
// Read order is not observable to parsing (each key writes a distinct member and
// .value / parse_vector have no cross-key side effects) and the struct layout is
// untouched (ABI red line), but read order is what token-for-token parity with
// the pre-change body requires, so read order is what this list pins.
//
// Authored in the tools/maintenance/dto_schema X-macro form but intentionally
// NOT registered in the dto_schema generator, per I58: the generator
// unconditionally emits a semantically misplaced gym_envs/scenario_loader/
// _generated Python builder per schema and its freshness gate hardcodes a
// registration list, while this is a C++-only content-loader parse map with no
// scenario_loader face. It stays a hand-authored .inc pinned by
// tests/architecture/content/test_aero_tuning_fields_inc.py, whose anchor is the
// AeroTuning declaration itself.

#if !defined(EF_AERO_TUNING_FIELD) || !defined(EF_AERO_TUNING_VECTOR_FIELD)
#error "define EF_AERO_TUNING_FIELD and EF_AERO_TUNING_VECTOR_FIELD before including aero_tuning_fields.inc"
#endif

EF_AERO_TUNING_FIELD(double, cl_alpha_per_deg, 0.1)
EF_AERO_TUNING_FIELD(double, cl0, 0.0)
EF_AERO_TUNING_FIELD(double, cd0_clean, 0.02)
EF_AERO_TUNING_FIELD(double, induced_drag_k, 0.1)
EF_AERO_TUNING_FIELD(double, cm_alpha_per_rad, -0.8)
EF_AERO_TUNING_FIELD(double, cm_q, -12.0)
EF_AERO_TUNING_FIELD(double, alpha_stall_clean_deg, 15.0)
EF_AERO_TUNING_FIELD(double, alpha_stall_flaps_full_deg, 21.0)
EF_AERO_TUNING_FIELD(double, alpha_peak_offset_deg, 8.0)
EF_AERO_TUNING_FIELD(double, alpha_deep_offset_deg, 18.0)
EF_AERO_TUNING_FIELD(double, cl_peak_clean, 1.25)
EF_AERO_TUNING_FIELD(double, cl_peak_flaps_full, 1.70)
EF_AERO_TUNING_FIELD(double, cl_deep_clean, 0.22)
EF_AERO_TUNING_FIELD(double, cl_deep_flaps_full, 0.32)
EF_AERO_TUNING_FIELD(double, pitch_break_onset_deg, 16.0)
EF_AERO_TUNING_FIELD(double, pitch_break_full_deg, 28.0)
EF_AERO_TUNING_FIELD(double, pitch_break_cm_nose_down, -0.35)
EF_AERO_TUNING_FIELD(double, post_stall_damp_floor, 0.25)
EF_AERO_TUNING_FIELD(double, aoa_rate_pitch_break_gain, 0.0035)
EF_AERO_TUNING_FIELD(double, elevator_max_deflection_deg, 25.0)
EF_AERO_TUNING_FIELD(double, aileron_max_deflection_deg, 21.5)
EF_AERO_TUNING_FIELD(double, rudder_max_deflection_deg, 30.0)
EF_AERO_TUNING_FIELD(double, cm_delta_e_per_rad, 1.2)
EF_AERO_TUNING_FIELD(double, cl_delta_a_per_rad, 0.10)
EF_AERO_TUNING_FIELD(double, cn_delta_r_per_rad, 0.13)
EF_AERO_TUNING_FIELD(double, fbw_elevator_cmd_per_rate_err, 0.9)
EF_AERO_TUNING_FIELD(double, fbw_aileron_cmd_per_rate_err, 1.2)
EF_AERO_TUNING_FIELD(double, fbw_rudder_cmd_per_rate_err, 1.2)
EF_AERO_TUNING_FIELD(double, ari_rudder_cmd_per_aileron_cmd, 0.25)
EF_AERO_TUNING_FIELD(bool, fbw_g_command_enabled, true)
EF_AERO_TUNING_FIELD(double, fbw_g_command_neutral, 1.0)
EF_AERO_TUNING_FIELD(double, fbw_g_command_max, 8.0)
EF_AERO_TUNING_FIELD(double, fbw_g_command_min, -2.0)
EF_AERO_TUNING_FIELD(double, fbw_pitch_rate_per_g_err, 0.30)
EF_AERO_TUNING_FIELD(double, actuator_tau_elevator_s, 0.10)
EF_AERO_TUNING_FIELD(double, actuator_tau_aileron_s, 0.08)
EF_AERO_TUNING_FIELD(double, actuator_tau_rudder_s, 0.12)
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, mach_breakpoints, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, cl_alpha_scale_vs_mach, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, cd0_add_vs_mach, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, induced_drag_scale_vs_mach, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, cm_alpha_scale_vs_mach, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, stall_alpha_delta_deg_vs_mach, {})
EF_AERO_TUNING_VECTOR_FIELD(std::vector<double>, control_effectiveness_scale_vs_mach, {})

#undef EF_AERO_TUNING_FIELD
#undef EF_AERO_TUNING_VECTOR_FIELD
