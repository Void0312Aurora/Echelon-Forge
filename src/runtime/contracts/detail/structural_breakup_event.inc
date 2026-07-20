// X-macro list of StructuralBreakupEvent fields.
//
// Consumers define EF_STRUCTURAL_BREAKUP_EVENT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_STRUCTURAL_BREAKUP_EVENT_FIELD(LethalityChainHeader, header, {})
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(std::string, breakup_state, "none")
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(std::string, break_mode, "none")
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(std::string, detached_part_ref, {})
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(std::uint32_t, detached_part_count, 0)
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(bool, airframe_breakup, false)
EF_STRUCTURAL_BREAKUP_EVENT_FIELD(std::uint64_t, cause_event_id, 0)

#undef EF_STRUCTURAL_BREAKUP_EVENT_FIELD
