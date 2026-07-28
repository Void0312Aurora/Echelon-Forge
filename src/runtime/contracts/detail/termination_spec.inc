// X-macro list of TerminationSpec fields.
//
// Consumers define EF_TERMINATION_SPEC_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_TERMINATION_SPEC_FIELD(std::string, reason, "running")
EF_TERMINATION_SPEC_FIELD(std::string, reason_source, "simulation")
EF_TERMINATION_SPEC_FIELD(std::uint64_t, snapshot_version, 0)

#undef EF_TERMINATION_SPEC_FIELD
