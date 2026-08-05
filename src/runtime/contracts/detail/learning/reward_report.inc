// X-macro list of RewardReport fields.
//
// Consumers define EF_REWARD_REPORT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_REWARD_REPORT_FIELD(std::vector<RewardTerm>, fact_terms, {})
EF_REWARD_REPORT_FIELD(std::vector<RewardTerm>, shaping_terms, {})
EF_REWARD_REPORT_FIELD(std::uint64_t, fact_snapshot_version, 0)
EF_REWARD_REPORT_FIELD(std::string, term_owner, "split")

#undef EF_REWARD_REPORT_FIELD
