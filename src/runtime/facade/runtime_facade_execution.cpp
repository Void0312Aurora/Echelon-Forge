#include "runtime/facade/runtime_facade_internal.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace {

using namespace runtime_facade_internal;

ObservationBatchRequest
observation_request_from_step_request(const ExecutionBatchStepRequest &request) {
    return ObservationBatchRequest{
        .refs = refs_from_step_requests(request.step_requests),
        .include_agent_observations = request.include_agent_observations,
        .include_instrument_states = request.include_instrument_states,
    };
}

TaskingBatchRequest tasking_request_from_step_request(const ExecutionBatchStepRequest &request) {
    return TaskingBatchRequest{
        .refs = refs_from_step_requests(request.step_requests),
    };
}

std::uint64_t next_snapshot_version(std::size_t index) {
    return static_cast<std::uint64_t>(index + 1);
}

void add_reward_term_if_nonzero(std::vector<RewardTerm> *terms, const char *name, double value,
                                const char *owner = "simulation") {
    if (terms == nullptr || value == 0.0) {
        return;
    }
    terms->push_back(RewardTerm{
        .name = name,
        .value = value,
        .term_owner = owner,
    });
}

RewardReport reward_report_from_step_result(const ExecutionEpisodeControllerStepResult &step_result,
                                            std::uint64_t fact_snapshot_version) {
    RewardReport report{};
    report.fact_snapshot_version = fact_snapshot_version;
    report.fact_terms.push_back(RewardTerm{
        .name = "fact_snapshot_version",
        .value = static_cast<double>(fact_snapshot_version),
        .term_owner = "simulation",
    });

    if (!step_result.valid) {
        return report;
    }

    report.shaping_terms.push_back(RewardTerm{
        .name = "compiled_reward_total",
        .value = step_result.reward_total,
        .term_owner = "experiment",
    });

    if (step_result.controller_state.last_reward_total != step_result.reward_total) {
        add_reward_term_if_nonzero(&report.shaping_terms, "controller_reward_total",
                                   step_result.controller_state.last_reward_total, "experiment");
    }

    if (step_result.step_info_valid) {
        const auto &info = step_result.step_info;
        add_reward_term_if_nonzero(&report.fact_terms, "runway_cross_m", info.runway_cross_m);
        add_reward_term_if_nonzero(&report.fact_terms, "runway_along_m", info.runway_along_m);
        if (info.on_runway) {
            add_reward_term_if_nonzero(&report.fact_terms, "on_runway", 1.0);
        }
        if (info.airborne) {
            add_reward_term_if_nonzero(&report.fact_terms, "airborne", 1.0);
        }
        if (info.gear_collapsed) {
            add_reward_term_if_nonzero(&report.fact_terms, "gear_collapsed", 1.0);
        }
        add_reward_term_if_nonzero(&report.fact_terms, "gear_stress", info.gear_stress);
    }

    const auto &state = step_result.controller_state;
    add_reward_term_if_nonzero(&report.fact_terms, "termination_state_active",
                               state.last_termination_reason == "running" ? 0.0 : 1.0);
    add_reward_term_if_nonzero(&report.shaping_terms, "step_count",
                               static_cast<double>(state.step_count), "experiment");
    add_reward_term_if_nonzero(&report.shaping_terms, "reward_total", state.last_reward_total,
                               "experiment");
    if (step_result.structural_state_changed) {
        add_reward_term_if_nonzero(&report.shaping_terms, "structural_state_changed", 1.0,
                                   "orchestration");
    }

    return report;
}

TerminationSpec
termination_spec_from_step_result(const ExecutionEpisodeControllerStepResult &step_result,
                                  bool truncated, std::uint64_t snapshot_version) {
    TerminationSpec spec{};
    spec.reason = step_result.controller_state.last_termination_reason;
    spec.snapshot_version = snapshot_version;
    if (truncated) {
        spec.reason_source = "orchestration";
    } else if (step_result.terminated) {
        spec.reason_source = "simulation";
    } else {
        spec.reason_source = "policy";
    }
    return spec;
}

} // namespace

void RuntimeFacade::clear_execution_episode_batch() noexcept {
    (void)runtime_->inject(runtime::backend::InputBatch{
        .clear_execution_episode_controller = true,
    });
}

void RuntimeFacade::prime_execution_episode_batch(
    const std::vector<WorldEntityRef> &refs, const std::vector<ExecutionEpisodeState> &states) {
    (void)runtime_->inject(runtime::backend::InputBatch{
        .prime_execution_episode_controller = true,
        .execution_episode_refs = refs,
        .execution_episode_states = states,
    });
}

bool RuntimeFacade::execution_episode_ready(std::size_t world_index) const noexcept {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .world_index = world_index,
            .include_execution_episode_ready = true,
        })
        .execution_episode_ready;
}

std::vector<ExecutionEpisodeState>
RuntimeFacade::export_execution_episode_states(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_execution_episode_states = true,
        })
        .execution_episode_states;
}

std::vector<ExecutionEpisodeRuntimeProducts> RuntimeFacade::step_execution_products_batch(
    const std::vector<WorldExecutionEpisodeStepRequest> &requests) {
    return runtime_
        ->advance(runtime::backend::AdvanceRequest{
            .kind = runtime::backend::AdvanceKind::StepExecutionProducts,
            .execution_episode_requests = requests,
        })
        .execution_episode_products;
}

ExecutionBatchStepResult
RuntimeFacade::step_execution_batch(const ExecutionBatchStepRequest &request) {
    ExecutionBatchStepResult result{};
    result.step_results = runtime_
                              ->advance(runtime::backend::AdvanceRequest{
                                  .kind = runtime::backend::AdvanceKind::StepExecutionResults,
                                  .execution_episode_requests = request.step_requests,
                              })
                              .execution_episode_step_results;
    const std::vector<WorldEntityRef> step_refs = refs_from_step_requests(request.step_requests);
    result.execution_episode_states = runtime_
                                          ->export_state(runtime::backend::ExportRequest{
                                              .refs = step_refs,
                                              .include_execution_episode_states = true,
                                          })
                                          .execution_episode_states;
    result.rewards.reserve(result.step_results.size());
    result.terminated.reserve(result.step_results.size());
    result.truncated.reserve(result.step_results.size());
    result.status_vectors.reserve(result.step_results.size());
    result.termination_reasons.reserve(result.step_results.size());
    result.termination_specs.reserve(result.step_results.size());
    result.reward_breakdown_jsons.reserve(result.step_results.size());
    result.reward_reports.reserve(result.step_results.size());
    result.step_infos.reserve(result.step_results.size());
    result.step_info_valid_flags.reserve(result.step_results.size());
    result.controller_state_changed_flags.reserve(result.step_results.size());
    for (std::size_t step_index = 0; step_index < result.step_results.size(); ++step_index) {
        const auto &step_result = result.step_results[step_index];
        const std::uint64_t snapshot_version = next_snapshot_version(step_index);
        result.rewards.push_back(step_result.reward_total);
        result.terminated.push_back(step_result.terminated);
        result.truncated.push_back(step_result.truncated);
        result.status_vectors.push_back(std::array<double, 4>{
            step_result.status0,
            step_result.status1,
            step_result.status2,
            step_result.status3,
        });
        result.termination_reasons.push_back(step_result.controller_state.last_termination_reason);
        result.termination_specs.push_back(termination_spec_from_step_result(
            step_result, step_result.truncated, snapshot_version));
        result.reward_breakdown_jsons.push_back(
            step_result.controller_state.last_reward_breakdown_json);
        result.reward_reports.push_back(
            reward_report_from_step_result(step_result, snapshot_version));
        result.step_infos.push_back(step_result.step_info);
        result.step_info_valid_flags.push_back(step_result.step_info_valid);
        result.controller_state_changed_flags.push_back(step_result.structural_state_changed);
    }
    result.observation_packet =
        build_observation_packet(observation_request_from_step_request(request));
    result.tasking_packet = build_tasking_packet(tasking_request_from_step_request(request));
    return result;
}
