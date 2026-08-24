#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_learning(nb::module_ &m) {
    nb::class_<RewardTerm> reward_term_class(m, "RewardTerm");
    reward_term_class.def(nb::init<>());
#define EF_REWARD_TERM_FIELD(type, name, default_value)                                            \
    reward_term_class.def_rw(#name, &RewardTerm::name);
#include "runtime/contracts/detail/learning/reward_term.inc"

    nb::class_<RewardReport> reward_report_class(m, "RewardReport");
    reward_report_class.def(nb::init<>());
#define EF_REWARD_REPORT_FIELD(type, name, default_value)                                          \
    reward_report_class.def_rw(#name, &RewardReport::name);
#include "runtime/contracts/detail/learning/reward_report.inc"

    nb::class_<TerminationSpec> termination_spec_class(m, "TerminationSpec");
    termination_spec_class.def(nb::init<>());
#define EF_TERMINATION_SPEC_FIELD(type, name, default_value)                                       \
    termination_spec_class.def_rw(#name, &TerminationSpec::name);
#include "runtime/contracts/detail/learning/termination_spec.inc"

    nb::class_<ObservationViewSpec> observation_view_spec_class(m, "ObservationViewSpec");
    observation_view_spec_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name, default_value)                                  \
    observation_view_spec_class.def_rw(#name, &ObservationViewSpec::name);
#include "runtime/contracts/detail/learning/observation_view_spec.inc"

    nb::class_<ObservationViewCompatibilityReport> observation_view_compatibility_report_class(
        m, "ObservationViewCompatibilityReport");
    observation_view_compatibility_report_class.def(nb::init<>());
#define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type, name, default_value)                  \
    observation_view_compatibility_report_class.def_rw(#name,                                      \
                                                       &ObservationViewCompatibilityReport::name);
#include "runtime/contracts/detail/learning/observation_view_compatibility_report.inc"

    m.def("evaluate_observation_view_checkpoint_compatibility",
          &evaluate_observation_view_checkpoint_compatibility, nb::arg("checkpoint"),
          nb::arg("provider"));
    m.def("make_exact_evaluation_cpu_reference_fidelity_request",
          &runtime::fidelity::make_exact_evaluation_cpu_reference_request);
    m.def("admit_fidelity_profile_request", &runtime::fidelity::admit_fidelity_profile_request,
          nb::arg("request"));
    m.def("validate_typed_platform_spawn_request", &validate_typed_platform_spawn_request,
          nb::arg("request"));
    m.def("information_state_source_has_valid_label", &information_state_source_has_valid_label,
          nb::arg("source"));
    m.def("agent_role_has_maintained_authority_shape", &agent_role_has_maintained_authority_shape,
          nb::arg("role"));
    m.def("agent_role_action_interface_matches_authority_scope",
          &agent_role_action_interface_matches_authority_scope, nb::arg("role"));
    m.def("authorize_maintained_action_intent", &authorize_maintained_action_intent,
          nb::arg("role"), nb::arg("intent"));
    m.def("authorize_maintained_coordination_intent", &authorize_maintained_coordination_intent,
          nb::arg("role"), nb::arg("intent"));
    m.def("decision_belief_requires_diagnostics_only", &decision_belief_requires_diagnostics_only,
          nb::arg("belief"));
    m.def("decision_belief_has_valid_provenance", &decision_belief_has_valid_provenance,
          nb::arg("belief"));
}
