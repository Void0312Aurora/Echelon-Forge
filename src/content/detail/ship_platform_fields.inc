// Single-source X-macro field list for the ShipPlatform inner scalar keys read
// by parse_unit_json's ship_platform object block
// (content/unit_definition_loader.cpp), T11 loader table-drive bundle (this
// iteration). Each key's JSON name is byte-identical to its ShipPlatform
// member name (components/domains/naval/platform/ship_platform.h), and the
// "missing key keeps the existing value" default semantics is carried by the
// parse-side sp.value(#name, def.ship_platform.name) expansion, NOT by the
// default_value token recorded here (the I58 missile_tuning_fields.inc
// convention, not the I61 literal-default one): parse_unit_json resets
// def.ship_platform = {} immediately before the block, so the effective
// missing-key default is the struct initializer, whose exact token is mirrored
// here for review parity and future struct single-sourcing.
//
// The consumer defines the macro before including; the footer #undef's it:
//   EF_SHIP_PLATFORM_FIELD(cpp_type, name, default_value)
// Field order mirrors the ShipPlatform declaration order, which coincides with
// the historical hand-written read order. Expansion happens at the exact
// original seam inside the ship_platform if-block: JSON conversion can throw,
// so reordering a read changes which malformed key fails first on
// multi-bad-key input even though successful-input values are independent.
//
// This is deliberately a separate .inc from submarine_platform_fields.inc:
// the two platform families are distinct component structs with disjoint parse
// seams, and their same-named members (length_m, beam_m, draft_m,
// max_accel_mps2, max_decel_mps2, max_turn_rate_deg_s, crew) carry DIFFERENT
// struct default tokens per family, so a shared list would need family-tagged
// duplicate rows with conflicting default tokens and would break the
// one-struct/one-list review parity that the default token exists to provide.
//
// The object-presence flag (has_ship_platform), the def.ship_platform = {}
// reset, and the sp binding stay hand-written in parse_unit_json; only the
// repetitive member reads live here. Authored in the tools/maintenance/
// dto_schema X-macro form but intentionally NOT registered in the dto_schema
// generator (C++-only content-loader parse map with no scenario_loader Python
// builder; same rationale as I58). Pinned by
// tests/architecture/content/test_ship_submarine_platform_fields_inc.py
// (three-way closure: struct header == .inc == pinned table).

#if !defined(EF_SHIP_PLATFORM_FIELD)
#error "define EF_SHIP_PLATFORM_FIELD before including ship_platform_fields.inc"
#endif

EF_SHIP_PLATFORM_FIELD(double, displacement_light_kg, 0.0)
EF_SHIP_PLATFORM_FIELD(double, displacement_full_load_kg, 0.0)
EF_SHIP_PLATFORM_FIELD(double, length_m, 0.0)
EF_SHIP_PLATFORM_FIELD(double, beam_m, 0.0)
EF_SHIP_PLATFORM_FIELD(double, draft_m, 0.0)
EF_SHIP_PLATFORM_FIELD(double, height_above_waterline_m, 0.0)
EF_SHIP_PLATFORM_FIELD(double, max_speed_mps, 0.0)
EF_SHIP_PLATFORM_FIELD(double, economical_speed_mps, 0.0)
EF_SHIP_PLATFORM_FIELD(double, range_nm, 0.0)
EF_SHIP_PLATFORM_FIELD(double, range_speed_mps, 0.0)
EF_SHIP_PLATFORM_FIELD(double, max_accel_mps2, 0.12)
EF_SHIP_PLATFORM_FIELD(double, max_decel_mps2, 0.18)
EF_SHIP_PLATFORM_FIELD(double, max_turn_rate_deg_s, 2.0)
EF_SHIP_PLATFORM_FIELD(double, low_speed_turn_factor, 0.25)
EF_SHIP_PLATFORM_FIELD(double, steerageway_speed_mps, 0.5)
EF_SHIP_PLATFORM_FIELD(double, sea_state, 0.0)
EF_SHIP_PLATFORM_FIELD(double, wave_heading_deg, 0.0)
EF_SHIP_PLATFORM_FIELD(double, wave_period_s, 8.0)
EF_SHIP_PLATFORM_FIELD(double, max_roll_deg_sea_state_6, 8.0)
EF_SHIP_PLATFORM_FIELD(double, max_pitch_deg_sea_state_6, 3.0)
EF_SHIP_PLATFORM_FIELD(double, added_resistance_fraction_sea_state_6, 0.12)
EF_SHIP_PLATFORM_FIELD(int, crew, 0)

#undef EF_SHIP_PLATFORM_FIELD
