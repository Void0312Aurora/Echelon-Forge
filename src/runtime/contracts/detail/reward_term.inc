// X-macro list of RewardTerm fields.
//
// Consumers define EF_REWARD_TERM_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_REWARD_TERM_FIELD(std::string, name, {})
EF_REWARD_TERM_FIELD(double, value, 0.0)
EF_REWARD_TERM_FIELD(std::string, term_owner, "simulation")

#undef EF_REWARD_TERM_FIELD
