#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_window(nb::module_ &m) {
    nb::class_<RuntimeExperimentAncestry> runtime_experiment_ancestry_class(
        m, "RuntimeExperimentAncestry");
    runtime_experiment_ancestry_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name, default_value)                            \
    runtime_experiment_ancestry_class.def_rw(#name, &RuntimeExperimentAncestry::name);
#include "runtime/facade/detail/runtime/runtime_experiment_ancestry.inc"

    nb::class_<RuntimeExperimentResult> runtime_experiment_result_class(m,
                                                                        "RuntimeExperimentResult");
    runtime_experiment_result_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name, default_value)                              \
    runtime_experiment_result_class.def_rw(#name, &RuntimeExperimentResult::name);
#include "runtime/facade/detail/runtime/runtime_experiment_result.inc"

    // Schema-ownership note: RuntimeWindowActionRequest is not schema-generated. Its
    // header field list (runtime_facade_types.h) is ABI-ordered as
    // action_intent, source_layer, input_snapshot_version,
    // clock_domain_metadata, cadence_control -- but clock_domain_metadata
    // is a nested, never-bound type (no Python duplication to unify) and
    // this binding's registration order/coverage already diverges from
    // that ABI order (cadence_control before source_layer/
    // input_snapshot_version; clock_domain_metadata omitted). Left
    // hand-written and skipped from schema ownership; see the binding-schema
    // audit for the recorded skip rationale. Its nested
    // CadenceControl type is independently schema-owned below.
    nb::class_<RuntimeWindowActionRequest>(m, "RuntimeWindowActionRequest")
        .def(nb::init<>())
        .def_rw("action_intent", &RuntimeWindowActionRequest::action_intent)
        .def_rw("cadence_control", &RuntimeWindowActionRequest::cadence_control)
        .def_rw("source_layer", &RuntimeWindowActionRequest::source_layer)
        .def_rw("input_snapshot_version", &RuntimeWindowActionRequest::input_snapshot_version);

    nb::class_<RuntimeWindowInputRecord> runtime_window_input_record_class(
        m, "RuntimeWindowInputRecord");
    runtime_window_input_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value)                            \
    runtime_window_input_record_class.def_rw(#name, &RuntimeWindowInputRecord::name);
#include "runtime/facade/detail/window/runtime_window_input_record.inc"

    nb::class_<RuntimeWindowSchedulingContext> runtime_window_scheduling_context_class(
        m, "RuntimeWindowSchedulingContext");
    runtime_window_scheduling_context_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value)                      \
    runtime_window_scheduling_context_class.def_rw(#name, &RuntimeWindowSchedulingContext::name);
#include "runtime/facade/detail/window/runtime_window_scheduling_context.inc"

    nb::class_<RuntimeWindowBarrierRecord> runtime_window_barrier_record_class(
        m, "RuntimeWindowBarrierRecord");
    runtime_window_barrier_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value)                          \
    runtime_window_barrier_record_class.def_rw(#name, &RuntimeWindowBarrierRecord::name);
#include "runtime/facade/detail/window/runtime_window_barrier_record.inc"

    nb::class_<RuntimeWindowVisibilityRecord> runtime_window_visibility_record_class(
        m, "RuntimeWindowVisibilityRecord");
    runtime_window_visibility_record_class.def(nb::init<>());
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value)                       \
    runtime_window_visibility_record_class.def_rw(#name, &RuntimeWindowVisibilityRecord::name);
#include "runtime/facade/detail/window/runtime_window_visibility_record.inc"

    // Binding-order note: the RuntimeWindowNodeExecutionRecord/CadenceControl/
    // Cadence/CadenceConfig/CadenceTraceRecord/Request/Result bindings
    // below have long registered properties out of the header's ABI
    // declaration order (several alphabetically); left hand-written and
    // skipped from binding-side schema ownership so registration order/
    // dir() sequence stays byte-for-byte unchanged. Each struct's C++
    // field list is still schema-owned on the header side (see
    // runtime_facade_types.h); see the binding-schema audit for the
    // recorded partial-coverage rationale.
    nb::class_<RuntimeWindowNodeExecutionRecord>(m, "RuntimeWindowNodeExecutionRecord")
        .def(nb::init<>())
        .def_rw("barrier_order", &RuntimeWindowNodeExecutionRecord::barrier_order)
        .def_rw("clock_domain", &RuntimeWindowNodeExecutionRecord::clock_domain)
        .def_rw("clock_merge_policy", &RuntimeWindowNodeExecutionRecord::clock_merge_policy)
        .def_rw("decision_barrier_id", &RuntimeWindowNodeExecutionRecord::decision_barrier_id)
        .def_rw("decision_reason", &RuntimeWindowNodeExecutionRecord::decision_reason)
        .def_rw("execution_state", &RuntimeWindowNodeExecutionRecord::execution_state)
        .def_rw("node_id", &RuntimeWindowNodeExecutionRecord::node_id)
        .def_rw("read_snapshot_policy", &RuntimeWindowNodeExecutionRecord::read_snapshot_policy)
        .def_rw("source_snapshot_version",
                &RuntimeWindowNodeExecutionRecord::source_snapshot_version)
        .def_rw("source_time_s", &RuntimeWindowNodeExecutionRecord::source_time_s)
        .def_rw("target_window_id", &RuntimeWindowNodeExecutionRecord::target_window_id)
        .def_rw("trigger_source", &RuntimeWindowNodeExecutionRecord::trigger_source)
        .def_rw("write_commit_policy", &RuntimeWindowNodeExecutionRecord::write_commit_policy)
        .def_rw("visible_input_count", &RuntimeWindowNodeExecutionRecord::visible_input_count);

    nb::class_<RuntimeWindowActionRequest::CadenceControl>(m, "RuntimeWindowCadenceControl")
        .def(nb::init<>())
        .def_rw("enabled", &RuntimeWindowActionRequest::CadenceControl::enabled)
        .def_rw("expiry_time_s", &RuntimeWindowActionRequest::CadenceControl::expiry_time_s)
        .def_rw("has_expiry_time", &RuntimeWindowActionRequest::CadenceControl::has_expiry_time)
        .def_rw("hold_policy", &RuntimeWindowActionRequest::CadenceControl::hold_policy)
        .def_rw("source_cadence_domain",
                &RuntimeWindowActionRequest::CadenceControl::source_cadence_domain)
        .def_rw("source_tick", &RuntimeWindowActionRequest::CadenceControl::source_tick);

    nb::class_<RuntimeWindowCadence>(m, "RuntimeWindowCadence")
        .def(nb::init<>())
        .def_rw("barrier_id", &RuntimeWindowCadence::barrier_id)
        .def_rw("domain", &RuntimeWindowCadence::domain)
        .def_rw("interval_s", &RuntimeWindowCadence::interval_s)
        .def_rw("merge_policy", &RuntimeWindowCadence::merge_policy)
        .def_rw("tick_count", &RuntimeWindowCadence::tick_count);

    nb::class_<RuntimeWindowCadenceConfig>(m, "RuntimeWindowCadenceConfig")
        .def(nb::init<>())
        .def_rw("domains", &RuntimeWindowCadenceConfig::domains)
        .def_rw("window_duration_s", &RuntimeWindowCadenceConfig::window_duration_s);

    nb::class_<RuntimeWindowCadenceTraceRecord>(m, "RuntimeWindowCadenceTraceRecord")
        .def(nb::init<>())
        .def_rw("barrier_id", &RuntimeWindowCadenceTraceRecord::barrier_id)
        .def_rw("cadence_merge_policy", &RuntimeWindowCadenceTraceRecord::cadence_merge_policy)
        .def_rw("clock_domain", &RuntimeWindowCadenceTraceRecord::clock_domain)
        .def_rw("clock_merge_policy", &RuntimeWindowCadenceTraceRecord::clock_merge_policy)
        .def_rw("decision", &RuntimeWindowCadenceTraceRecord::decision)
        .def_rw("decision_reason", &RuntimeWindowCadenceTraceRecord::decision_reason)
        .def_rw("deferred", &RuntimeWindowCadenceTraceRecord::deferred)
        .def_rw("diagnostics_only", &RuntimeWindowCadenceTraceRecord::diagnostics_only)
        .def_rw("domain", &RuntimeWindowCadenceTraceRecord::domain)
        .def_rw("expired", &RuntimeWindowCadenceTraceRecord::expired)
        .def_rw("held", &RuntimeWindowCadenceTraceRecord::held)
        .def_rw("node_id", &RuntimeWindowCadenceTraceRecord::node_id)
        .def_rw("relation", &RuntimeWindowCadenceTraceRecord::relation)
        .def_rw("source", &RuntimeWindowCadenceTraceRecord::source)
        .def_rw("tick", &RuntimeWindowCadenceTraceRecord::tick);

    nb::class_<RuntimeWindowRequest>(m, "RuntimeWindowRequest")
        .def(nb::init<>())
        .def_rw("window_id", &RuntimeWindowRequest::window_id)
        .def_rw("world_id", &RuntimeWindowRequest::world_id)
        .def_rw("source_time_s", &RuntimeWindowRequest::source_time_s)
        .def_rw("action_requests", &RuntimeWindowRequest::action_requests)
        .def_rw("cadence_config", &RuntimeWindowRequest::cadence_config)
        .def_rw("observation_request", &RuntimeWindowRequest::observation_request)
        .def_rw("engagement_request", &RuntimeWindowRequest::engagement_request)
        .def_rw("export_observation", &RuntimeWindowRequest::export_observation)
        .def_rw("export_engagement", &RuntimeWindowRequest::export_engagement)
        .def_rw("export_diagnostics", &RuntimeWindowRequest::export_diagnostics);

    nb::class_<RuntimeWindowResult>(m, "RuntimeWindowResult")
        .def(nb::init<>())
        .def_rw("context", &RuntimeWindowResult::context)
        .def_rw("barrier_trace", &RuntimeWindowResult::barrier_trace)
        .def_rw("cadence_config", &RuntimeWindowResult::cadence_config)
        .def_rw("cadence_trace", &RuntimeWindowResult::cadence_trace)
        .def_rw("visibility_trace", &RuntimeWindowResult::visibility_trace)
        .def_rw("executed_nodes", &RuntimeWindowResult::executed_nodes)
        .def_rw("injected_inputs", &RuntimeWindowResult::injected_inputs)
        .def_rw("observation_packet", &RuntimeWindowResult::observation_packet)
        .def_rw("engagement_packet", &RuntimeWindowResult::engagement_packet)
        .def_rw("diagnostics_traces", &RuntimeWindowResult::diagnostics_traces);
}
