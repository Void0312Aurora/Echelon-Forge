// Single-source X-macro field list for the purely-mechanical direct top-level
// scalar keys read by parse_unit_json (content/unit_definition_loader.cpp),
// T11 slice 4 bundle 2 / I61. This is the direct-key sibling of the I58
// missile_tuning_fields.inc precedent.
//
// SCOPE (the mechanical subset, adjudicated against the I52 survey section 1.1
// "54 direct keys" table): a key lives here only if its read is the single-line
// scalar form `def.<member> = entry.value("<key>", <literal-default>);` with the
// JSON key byte-identical to its UnitDefinition member name, a literal default,
// and NO escape-hatch / object-block / has_*-flag / clamp / fallback coupling.
// Every other direct key (30 object blocks, the engine flat-vs-nested and the
// four-sensor and missile-tuning families, the has_* flags paired with object
// blocks, the clamped/fallback data_link_max_* ints, the validated `type`
// discriminant, and `name`'s type-string fallback default) stays hand-written
// in parse_unit_json and is intentionally absent here. The absence set is
// pinned by tests/architecture/content/test_unit_definition_direct_fields_inc.py.
//
// Consumers define both phase macros before including; the footer #undef's
// them. A consumer activates one phase and defines the other as a no-op so the
// two reads stay at their exact pre-I61 parse positions (including fail-first
// behavior for malformed multi-key input):
//   EF_UNIT_DIRECT_EARLY_FIELD(cpp_type, name, default_value)
//   EF_UNIT_DIRECT_DATA_LINK_FIELD(cpp_type, name, default_value)
//
// Unlike I58 (whose parse expansion carries the "missing key keeps existing
// value" default via src.value(key, current) and treats the default_value token
// as struct-init review parity only), parse_unit_json's hand-written reads use
// a *literal* default, so here the default_value token IS consumed by the parse
// expansion: a scalar row must expand token-for-token to the exact pre-I61
// hand-written statement `def.<member> = entry.value("<key>", <literal>);`. The
// literal also mirrors the UnitDefinition member's content-load default for
// review/future struct single-sourcing.
//
// Field order mirrors the I52 survey section 1.1 ascending row order for the
// converged keys. Expansion phase is part of the contract: JSON conversion can
// throw, so moving a read across another read changes which malformed key fails
// first even when successful-input values are otherwise independent.

#if !defined(EF_UNIT_DIRECT_EARLY_FIELD)
#error "define EF_UNIT_DIRECT_EARLY_FIELD before including unit_definition_direct_fields.inc"
#endif
#if !defined(EF_UNIT_DIRECT_DATA_LINK_FIELD)
#error "define EF_UNIT_DIRECT_DATA_LINK_FIELD before including unit_definition_direct_fields.inc"
#endif

EF_UNIT_DIRECT_EARLY_FIELD(double, mass_kg, 0.0)
EF_UNIT_DIRECT_DATA_LINK_FIELD(int, data_link_network_id, 0)

#undef EF_UNIT_DIRECT_EARLY_FIELD
#undef EF_UNIT_DIRECT_DATA_LINK_FIELD
