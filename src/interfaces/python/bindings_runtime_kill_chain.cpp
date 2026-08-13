#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_kill_chain(nb::module_ &m) {
    nb::class_<KillChainApproachFact> kill_chain_approach_fact_class(m, "KillChainApproachFact");
    kill_chain_approach_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_APPROACH_FACT_FIELD(type, name, default_value)                               \
    kill_chain_approach_fact_class.def_rw(#name, &KillChainApproachFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_approach_fact.inc"

    nb::class_<KillChainFuzeDecision> kill_chain_fuze_decision_class(m, "KillChainFuzeDecision");
    kill_chain_fuze_decision_class.def(nb::init<>());
#define EF_KILL_CHAIN_FUZE_DECISION_FIELD(type, name, default_value)                               \
    kill_chain_fuze_decision_class.def_rw(#name, &KillChainFuzeDecision::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_fuze_decision.inc"

    nb::class_<KillChainComponentLoadFact> kill_chain_component_load_fact_class(
        m, "KillChainComponentLoadFact");
    kill_chain_component_load_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_COMPONENT_LOAD_FACT_FIELD(type, name, default_value)                         \
    kill_chain_component_load_fact_class.def_rw(#name, &KillChainComponentLoadFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_component_load_fact.inc"

    nb::class_<KillChainWarheadLoadField> kill_chain_warhead_load_field_class(
        m, "KillChainWarheadLoadField");
    kill_chain_warhead_load_field_class.def(nb::init<>());
#define EF_KILL_CHAIN_WARHEAD_LOAD_FIELD_FIELD(type, name, default_value)                          \
    kill_chain_warhead_load_field_class.def_rw(#name, &KillChainWarheadLoadField::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_warhead_load_field.inc"

    nb::class_<KillChainTargetSusceptibility> kill_chain_target_susceptibility_class(
        m, "KillChainTargetSusceptibility");
    kill_chain_target_susceptibility_class.def(nb::init<>());
#define EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(type, name, default_value)                       \
    kill_chain_target_susceptibility_class.def_rw(#name, &KillChainTargetSusceptibility::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_target_susceptibility.inc"

    nb::class_<KillChainComponentResponseFact> kill_chain_component_response_fact_class(
        m, "KillChainComponentResponseFact");
    kill_chain_component_response_fact_class.def(nb::init<>());
#define EF_KILL_CHAIN_COMPONENT_RESPONSE_FACT_FIELD(type, name, default_value)                     \
    kill_chain_component_response_fact_class.def_rw(#name, &KillChainComponentResponseFact::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_component_response_fact.inc"

    nb::class_<KillChainConsequenceProjection> kill_chain_consequence_projection_class(
        m, "KillChainConsequenceProjection");
    kill_chain_consequence_projection_class.def(nb::init<>());
#define EF_KILL_CHAIN_CONSEQUENCE_PROJECTION_FIELD(type, name, default_value)                      \
    kill_chain_consequence_projection_class.def_rw(#name, &KillChainConsequenceProjection::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_consequence_projection.inc"

    nb::class_<KillChainRuntimeFacade> kill_chain_runtime_facade_class(m, "KillChainRuntimeFacade");
    kill_chain_runtime_facade_class.def(nb::init<>());
#define EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(type, name, default_value)                              \
    kill_chain_runtime_facade_class.def_rw(#name, &KillChainRuntimeFacade::name);
#include "runtime/contracts/detail/kill_chain/kill_chain_runtime_facade.inc"

    m.def("make_kill_chain_runtime_facade", &make_kill_chain_runtime_facade, nb::arg("effects"));

    nb::class_<DamageReport> damage_report_class(m, "DamageReport");
    damage_report_class.def(nb::init<>());
#define EF_DAMAGE_REPORT_FIELD(type, name, default_value)                                          \
    damage_report_class.def_rw(#name, &DamageReport::name);
#include "runtime/contracts/detail/damage/damage_report.inc"

    nb::class_<DiagnosticsTrace> diagnostics_trace_class(m, "DiagnosticsTrace");
    diagnostics_trace_class.def(nb::init<>());
#define EF_DIAGNOSTICS_TRACE_FIELD(type, name, default_value)                                      \
    diagnostics_trace_class.def_rw(#name, &DiagnosticsTrace::name);
#include "runtime/contracts/detail/engagement/diagnostics_trace.inc"
}
