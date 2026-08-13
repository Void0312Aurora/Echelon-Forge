// Single-source X-macro field list for EngineTuning's JSON parse (T11, this
// iteration). Owns the 16 purely-mechanical keys read by
// parse_engine_tuning_json_fields (content/unit_definition_loader.cpp). This is
// the engine sibling of the I58 missile_tuning_fields.inc and I66
// aero_tuning_fields.inc precedents and follows their scope-adjudication
// discipline.
//
// SCOPE (the mechanical subset, adjudicated member-by-member against the
// EngineTuning declaration in
// components/domains/air/platform/flight_dynamics_tuning.h): a key lives here
// only if its pre-change read is the exact single-line form
//   tuning.<member> = src.value("<member>", tuning.<member>);
// with the JSON key byte-identical to the member name and NO escape-hatch /
// object-block / has_*-flag / clamp / fallback coupling. All 16 non-`enabled`
// members qualify; the struct has no vector members, so unlike the missile and
// aero lists this file declares a single macro (see SINGLE MACRO below).
//
// DELIBERATELY ABSENT -- `enabled`. It is the one EngineTuning member read by
// the helper that is not mechanical: its pre-change read is
//   tuning.enabled = src.value("enabled", true);
// i.e. a *literal* `true` default, not the "missing key keeps the existing
// value" default the other 16 keys use. That literal is load-bearing for the
// engine.tuning / engine_tuning codec escape hatch (census red line "codec
// escape hatches"), exactly as for AeroTuning: both call sites seed the struct
// from the flight_dynamics::default_engine_tuning() preset and then merge, and
// a present tuning object with no "enabled" key must still come out enabled.
// The top-level engine_tuning call site additionally *branches* on
// tuning.enabled to decide whether to re-seed before merging on top of an
// engine.tuning block, so the member's semantics are doubly non-mechanical.
// Folding it into the scalar row shape below would silently change its default
// from `true` to the seeded value, so it stays hand-written directly above the
// include. Absence is pinned by
// tests/architecture/content/test_tuning_fields_inc.py.
//
// SINGLE MACRO. EngineTuning declares only bool/double members -- no
// std::vector<double> tables -- so this list defines only the scalar macro and
// the loader consumes it in a single pass (there is no parse_vector lambda to
// order around, hence no two-pass include). If EngineTuning ever gains a vector
// member, the guard test's struct anchor goes red (it pins the member type set
// to {bool, double}) and the adjudication, macro shape, and pass structure must
// be revisited rather than silently extended.
//
// ANGLE-BRACKET-COMMA ADJUDICATION (census red line "X-macro comma blockers",
// I31 precedent). Every EngineTuning member was checked: none is templated at
// all, so nothing can be mis-split by the preprocessor and no member is held on
// comma grounds. No type-alias exemption is used anywhere in this list.
//
// Consumers define the macro before including; the footer #undef's it:
//   EF_ENGINE_TUNING_FIELD(cpp_type, name, default_value)  scalar key
//
// DEFAULT_VALUE TOKEN: parity-only, NOT parse-consumed. As in I58/I66 (and
// unlike the I61 unit_definition_direct_fields.inc bundle, whose hand-written
// reads used literal defaults), the "missing key keeps the existing value"
// semantics is carried by the parse-side src.value(key, current) expansion, so
// the default_value token recorded here is never expanded into the parse. It
// mirrors the EngineTuning declaration's own initializer for review parity and
// future struct single-sourcing, and the guard test pins it to that
// initializer verbatim.
//
// FIELD ORDER mirrors both the EngineTuning declaration order and the
// historical hand-written read order, which for this struct are identical
// (unlike AeroTuning, whose read order deviated). Read order is not observable
// to parsing (each key writes a distinct member and .value has no cross-key
// side effects), but it is what token-for-token parity with the pre-change
// body requires, so it is what this list pins.
//
// Authored in the tools/maintenance/dto_schema X-macro form but intentionally
// NOT registered in the dto_schema generator, per I58/I66: the generator
// unconditionally emits a semantically misplaced gym_envs/scenario_loader/
// _generated Python builder per schema and its freshness gate hardcodes a
// registration list, while this is a C++-only content-loader parse map with no
// scenario_loader face. It stays a hand-authored .inc pinned by
// tests/architecture/content/test_tuning_fields_inc.py, whose anchor is
// the EngineTuning declaration itself.

#if !defined(EF_ENGINE_TUNING_FIELD)
#error "define EF_ENGINE_TUNING_FIELD before including engine_tuning_fields.inc"
#endif

EF_ENGINE_TUNING_FIELD(double, mil_thrust_n, 0.0)
EF_ENGINE_TUNING_FIELD(double, ab_thrust_n, 0.0)
EF_ENGINE_TUNING_FIELD(double, throttle_ab_threshold, 0.9)
EF_ENGINE_TUNING_FIELD(double, throttle_idle_bias, 0.08)
EF_ENGINE_TUNING_FIELD(double, tau_spool_up_s, 2.5)
EF_ENGINE_TUNING_FIELD(double, tau_spool_down_s, 1.5)
EF_ENGINE_TUNING_FIELD(double, tau_ab_light_s, 1.0)
EF_ENGINE_TUNING_FIELD(double, tau_ab_extinguish_s, 0.5)
EF_ENGINE_TUNING_FIELD(double, ram_rise_gain, 0.3)
EF_ENGINE_TUNING_FIELD(double, ram_rise_mach_cap, 1.2)
EF_ENGINE_TUNING_FIELD(double, ram_decay_start_mach, 1.5)
EF_ENGINE_TUNING_FIELD(double, ram_decay_gain, 0.2)
EF_ENGINE_TUNING_FIELD(double, thrust_sigma_exponent, 1.0)
EF_ENGINE_TUNING_FIELD(double, thrust_theta_exponent, 0.0)
EF_ENGINE_TUNING_FIELD(double, tsfc_mil_kg_per_nh, 0.10)
EF_ENGINE_TUNING_FIELD(double, tsfc_ab_kg_per_nh, 0.25)

#undef EF_ENGINE_TUNING_FIELD
