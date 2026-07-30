#include "runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace runtime::cuda_resident::replay {

namespace {

void append_token(std::string &out, std::string_view value) {
    out += std::to_string(value.size());
    out.push_back(':');
    out.append(value);
    out.push_back('|');
}

void append_double_token(std::string &out, double value) {
    append_token(out, replay_canonical_double(value));
}

void append_pilot_action(std::string &out, const PilotAction &action) {
    append_double_token(out, action.stick_pitch);
    append_double_token(out, action.stick_roll);
    append_double_token(out, action.rudder);
    append_double_token(out, action.throttle);
    append_double_token(out, static_cast<double>(action.gear_handle));
    append_double_token(out, static_cast<double>(action.flaps));
    append_double_token(out, static_cast<double>(action.speedbrake));
    append_double_token(out, action.brake);
    append_token(out, replay_canonical_bool(action.brake_left));
    append_token(out, replay_canonical_bool(action.brake_right));
    append_token(out, replay_canonical_bool(action.radar_active));
    append_double_token(out, action.radar_scan_az);
    append_double_token(out, action.radar_scan_el);
    append_token(out, replay_canonical_bool(action.tms_up));
    append_token(out, replay_canonical_bool(action.master_arm));
    append_token(out, replay_canonical_bool(action.fire_weapon));
    append_token(out, replay_canonical_bool(action.fire_gun));
    append_token(out, std::to_string(action.weapon_select_id));
    append_token(out, replay_canonical_bool(action.jettison_emergency));
    append_token(out, replay_canonical_bool(action.program_chaff));
    append_token(out, replay_canonical_bool(action.program_flare));
    append_token(out, replay_canonical_bool(action.active));
}

std::size_t count_frames(const ReplayLaneResult &result, std::size_t window_index,
                         std::string_view barrier_id) {
    return static_cast<std::size_t>(
        std::count_if(result.frames.begin(), result.frames.end(), [&](const ReplayLaneFrame &frame) {
            return frame.window_index == window_index && frame.barrier_id == barrier_id;
        }));
}

const ReplayLaneFrame *find_unique_frame(const ReplayLaneResult &result, std::size_t window_index,
                                         std::string_view barrier_id) {
    if (count_frames(result, window_index, barrier_id) != 1) return nullptr;
    const auto found = std::find_if(
        result.frames.begin(), result.frames.end(), [&](const ReplayLaneFrame &frame) {
            return frame.window_index == window_index && frame.barrier_id == barrier_id;
        });
    return found == result.frames.end() ? nullptr : &(*found);
}

std::size_t count_fields(const ReplayLaneFrame *frame, std::size_t world_index,
                         std::string_view field_family, std::string_view field_path) {
    if (frame == nullptr) return 0;
    return static_cast<std::size_t>(
        std::count_if(frame->fields.begin(), frame->fields.end(), [&](const ReplayFieldValue &field) {
            return field.world_index == world_index && field.field_family == field_family &&
                   field.field_path == field_path;
        }));
}

const ReplayFieldValue *find_unique_field(const ReplayLaneFrame *frame, std::size_t world_index,
                                          std::string_view field_family,
                                          std::string_view field_path) {
    if (count_fields(frame, world_index, field_family, field_path) != 1) return nullptr;
    const auto found = std::find_if(
        frame->fields.begin(), frame->fields.end(), [&](const ReplayFieldValue &field) {
            return field.world_index == world_index && field.field_family == field_family &&
                   field.field_path == field_path;
        });
    return found == frame->fields.end() ? nullptr : &(*found);
}

const parity::ParityBudgetBarrierRule *find_barrier_rule(std::string_view barrier_id) {
    const auto &rules = parity::resident_candidate_barrier_contract();
    const auto found = std::find_if(
        rules.begin(), rules.end(), [&](const parity::ParityBudgetBarrierRule &rule) {
            return rule.barrier_id == barrier_id;
        });
    return found == rules.end() ? nullptr : &(*found);
}

void append_unique(std::vector<std::string> &items, std::string_view value) {
    if (std::find(items.begin(), items.end(), value) == items.end()) {
        items.emplace_back(value);
    }
}

bool values_match(const parity::ParityBudgetSelectedFieldFamily &family,
                  const ReplayFieldValue &reference, const ReplayFieldValue &shadow) {
    if (!reference.available || !shadow.available) return false;
    if (family.comparator == parity::kParityComparatorExact) {
        return reference.canonical_value == shadow.canonical_value;
    }
    if (family.comparator != parity::kParityComparatorAbsoluteOrRelative ||
        !reference.numeric || !shadow.numeric || !std::isfinite(reference.numeric_value) ||
        !std::isfinite(shadow.numeric_value)) {
        return false;
    }
    const double difference = std::abs(reference.numeric_value - shadow.numeric_value);
    const double scale = std::max(std::abs(reference.numeric_value),
                                  std::abs(shadow.numeric_value));
    return difference <=
           std::max(family.absolute_tolerance, family.relative_tolerance * scale);
}

void append_mismatch(ReplayComparisonReport &report, std::size_t window_index,
                     std::size_t world_index, std::string_view barrier_id,
                     std::string_view field_family, std::string_view field_path,
                     std::string_view code, std::string_view expected,
                     std::string_view actual) {
    report.mismatches.push_back({
        .window_index = window_index,
        .world_index = world_index,
        .barrier_id = std::string(barrier_id),
        .field_family = std::string(field_family),
        .field_path = std::string(field_path),
        .mismatch_code = std::string(code),
        .expected = std::string(expected),
        .actual = std::string(actual),
    });
}

std::string build_stable_signature(const ReplayComparisonReport &report) {
    std::string signature;
    append_token(signature, report.run_id);
    append_token(signature, report.trace_signature);
    append_token(signature, report.backend_profile_id);
    append_token(signature, report.parity_budget_ref);
    append_token(signature, report.shadow_profile_id);
    append_token(signature, report.shadow_parity_budget_ref);
    append_token(signature, std::to_string(static_cast<int>(report.status)));
    append_token(signature, report.rejection_reason);
    append_token(signature, report.shadow_run_id);
    append_token(signature, report.sync_barrier_id);
    append_token(signature, report.mismatch_domain);
    append_token(signature, report.mismatch_summary);
    append_token(signature, std::to_string(report.coverage.expected_selected_field_count));
    append_token(signature, std::to_string(report.coverage.consumed_selected_field_count));
    append_token(signature, std::to_string(report.coverage.expected_field_instances));
    append_token(signature, std::to_string(report.coverage.expected_field_family_count));
    append_token(signature, std::to_string(report.coverage.expected_barrier_count));
    append_token(signature, std::to_string(report.coverage.selected_field_instances));
    append_token(signature, std::to_string(report.coverage.available_field_instances));
    append_token(signature, std::to_string(report.coverage.matched_field_instances));
    append_token(signature, std::to_string(report.coverage.mismatched_field_instances));
    append_token(signature, std::to_string(report.coverage.unavailable_field_instances));
    for (const auto version : report.reference_source_snapshot_versions) {
        append_token(signature, "reference:" + std::to_string(version));
    }
    for (const auto version : report.shadow_source_snapshot_versions) {
        append_token(signature, "shadow:" + std::to_string(version));
    }
    for (const auto &mismatch : report.mismatches) {
        append_token(signature, std::to_string(mismatch.window_index));
        append_token(signature, std::to_string(mismatch.world_index));
        append_token(signature, mismatch.barrier_id);
        append_token(signature, mismatch.field_family);
        append_token(signature, mismatch.field_path);
        append_token(signature, mismatch.mismatch_code);
        append_token(signature, mismatch.expected);
        append_token(signature, mismatch.actual);
    }
    return signature;
}

void validate_trace(const ReplayTrace &trace) {
    if (trace.run_id.empty()) throw std::invalid_argument("RB8 replay requires run_id");
    if (trace.backend_profile_id != kCudaResidentReplayProfileId) {
        throw std::invalid_argument("RB8 replay profile is not the frozen resident candidate");
    }
    if (trace.parity_budget_ref != kCudaResidentReplayBudgetRef) {
        throw std::invalid_argument("RB8 replay budget is not the frozen resident candidate");
    }
    if (trace.seeds.empty() || trace.seeds.size() != trace.spawns.size() ||
        trace.seeds.size() != trace.time_steps.size() || trace.windows.empty()) {
        throw std::invalid_argument("RB8 replay setup/window cardinalities are invalid");
    }
    for (std::size_t window = 0; window < trace.windows.size(); ++window) {
        if (trace.windows[window].actions.size() != trace.seeds.size() ||
            trace.windows[window].request_id.empty()) {
            throw std::invalid_argument("RB8 replay action window is incomplete");
        }
    }
    const auto *budget = parity::find_parity_budget_record(trace.parity_budget_ref);
    if (budget == nullptr) throw std::invalid_argument("RB8 replay budget is not registered");
    const auto validation = parity::validate_profile_owned_parity_budget(
        trace.backend_profile_id, parity::kParityBudgetProfileClassResidentState,
        trace.parity_budget_ref);
    if (!validation.valid || budget->selected_slice_fields !=
                                parity::resident_candidate_selected_slice_field_contract() ||
        budget->barrier_rules != parity::resident_candidate_barrier_contract()) {
        throw std::invalid_argument("RB8 replay budget failed its frozen contract");
    }
}

} // namespace

CudaResidentReplayHarness::CudaResidentReplayHarness(ReplayLaneRunner reference_runner,
                                                     ReplayLaneRunner shadow_runner)
    : reference_runner_(std::move(reference_runner)), shadow_runner_(std::move(shadow_runner)) {
    if (!reference_runner_ || !shadow_runner_) {
        throw std::invalid_argument("RB8 replay requires independent reference and shadow runners");
    }
}

std::string CudaResidentReplayHarness::trace_signature(const ReplayTrace &trace) {
    std::string signature;
    append_token(signature, trace.run_id);
    append_token(signature, trace.backend_profile_id);
    append_token(signature, trace.parity_budget_ref);
    for (const auto seed : trace.seeds) append_token(signature, std::to_string(seed));
    for (const auto &spawn : trace.spawns) {
        append_token(signature, std::to_string(spawn.world_index));
        append_token(signature, std::to_string(static_cast<int>(spawn.side)));
        append_token(signature, spawn.type_name);
        append_token(signature, spawn.entity_name);
        append_token(signature, replay_canonical_bool(spawn.is_agent));
        append_double_token(signature, spawn.x);
        append_double_token(signature, spawn.y);
        append_double_token(signature, spawn.z);
        append_double_token(signature, spawn.vx);
        append_double_token(signature, spawn.vy);
        append_double_token(signature, spawn.vz);
        append_double_token(signature, spawn.heading);
        append_double_token(signature, spawn.pitch);
        append_double_token(signature, spawn.roll);
        append_token(signature, replay_canonical_bool(spawn.ammo_override_enabled));
        append_token(signature, std::to_string(spawn.missiles_remaining));
        append_token(signature, std::to_string(spawn.max_missiles));
        append_token(signature, replay_canonical_bool(spawn.weapon_cooldown_override_enabled));
        append_double_token(signature, spawn.weapon_cooldown_s);
        append_double_token(signature, spawn.weapon_last_fire_time);
    }
    for (const double time_step : trace.time_steps) append_double_token(signature, time_step);
    for (const auto &window : trace.windows) {
        append_token(signature, window.request_id);
        for (const auto &action : window.actions) append_pilot_action(signature, action);
    }
    return signature;
}

ReplayComparisonReport CudaResidentReplayHarness::run(const ReplayTrace &trace) const {
    ReplayComparisonReport report{};
    report.run_id = trace.run_id;
    report.trace_signature = trace_signature(trace);
    report.backend_profile_id = trace.backend_profile_id;
    report.parity_budget_ref = trace.parity_budget_ref;
    report.shadow_run_id = trace.run_id + ".shadow";
    report.compared_profile_id = trace.backend_profile_id;
    report.candidate_promotion_blocked = true;
    report.maintained_claim_allowed = false;

    try {
        validate_trace(trace);
    } catch (const std::exception &error) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "invalid_trace";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "trace_identity";
        report.mismatch_summary = "invalid_trace";
        append_mismatch(report, 0, 0, "input_injection", "trace_identity", "trace",
                        "invalid_trace", "valid_frozen_trace", error.what());
        report.stable_signature = build_stable_signature(report);
        return report;
    }

    const auto *budget = parity::find_parity_budget_record(trace.parity_budget_ref);
    if (budget == nullptr) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "budget_disappeared";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "trace_identity";
        report.mismatch_summary = "budget_disappeared";
        report.stable_signature = build_stable_signature(report);
        return report;
    }
    report.parity_budget_version = budget->budget_version;
    report.comparison_reference = budget->comparison_reference;

    const std::string expected_trace_signature = report.trace_signature;
    ReplayLaneResult reference{};
    ReplayLaneResult shadow{};
    try {
        reference = reference_runner_(trace);
    } catch (const std::exception &error) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "reference_runner_failed";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "reference_runner";
        report.mismatch_summary = "reference_runner_failed";
        append_mismatch(report, 0, 0, "input_injection", "reference_runner", "runner",
                        "runner_failed", "completed", error.what());
        report.stable_signature = build_stable_signature(report);
        return report;
    } catch (...) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "reference_runner_failed";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "reference_runner";
        report.mismatch_summary = "reference_runner_failed";
        report.stable_signature = build_stable_signature(report);
        return report;
    }
    try {
        shadow = shadow_runner_(trace);
    } catch (const std::exception &error) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "shadow_runner_failed";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "shadow_runner";
        report.mismatch_summary = "shadow_runner_failed";
        append_mismatch(report, 0, 0, "input_injection", "shadow_runner", "runner",
                        "runner_failed", "completed", error.what());
        report.stable_signature = build_stable_signature(report);
        return report;
    } catch (...) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "shadow_runner_failed";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "shadow_runner";
        report.mismatch_summary = "shadow_runner_failed";
        report.stable_signature = build_stable_signature(report);
        return report;
    }

    if (!reference.completed || !shadow.completed) {
        report.status = ReplayRunStatus::rejected;
        report.rejection_reason = "lane_incomplete";
        report.sync_barrier_id = "input_injection";
        report.mismatch_domain = "lane_status";
        report.mismatch_summary = "lane_incomplete";
        append_mismatch(report, 0, 0, "input_injection", "lane_status", "completed",
                        "lane_incomplete", reference.failure_code, shadow.failure_code);
        report.stable_signature = build_stable_signature(report);
        return report;
    }

    if (reference.lane != ReplayLaneKind::cpu_reference ||
        shadow.lane != ReplayLaneKind::cuda_resident) {
        append_mismatch(report, 0, 0, "input_injection", "trace_identity", "lane_kind",
                        "invalid_lane", "cpu_reference/cuda_resident",
                        replay_lane_name(reference.lane) + "/" + replay_lane_name(shadow.lane));
    }
    if (reference.trace_signature != expected_trace_signature ||
        shadow.trace_signature != expected_trace_signature ||
        reference.trace_signature != shadow.trace_signature) {
        append_mismatch(report, 0, 0, "input_injection", "trace_identity", "trace_signature",
                        "trace_identity_mismatch", expected_trace_signature,
                        reference.trace_signature + "/" + shadow.trace_signature);
    }

    std::vector<std::string> expected_barriers;
    report.coverage.expected_field_family_count = budget->selected_slice_fields.size();
    for (const auto &family : budget->selected_slice_fields) {
        report.coverage.expected_selected_field_count += family.selected_fields.size();
        for (const auto &barrier_id : family.comparison_barriers) {
            append_unique(expected_barriers, barrier_id);
            report.coverage.expected_field_instances +=
                family.selected_fields.size() * trace.seeds.size() * trace.windows.size();
        }
    }
    report.coverage.expected_barrier_count = expected_barriers.size();

    bool frame_structure_valid = true;
    const auto validate_lane_frames = [&](const ReplayLaneResult &lane,
                                          std::string_view lane_name) {
        const std::size_t expected_frame_count = trace.windows.size() * expected_barriers.size();
        if (lane.frames.size() != expected_frame_count) {
            frame_structure_valid = false;
            append_mismatch(report, 0, 0, "input_injection", "frame_structure", "frame_count",
                            "frame_count_mismatch", std::to_string(expected_frame_count),
                            std::string(lane_name) + ":" + std::to_string(lane.frames.size()));
        }
        for (const auto &frame : lane.frames) {
            if (frame.window_index >= trace.windows.size() ||
                std::find(expected_barriers.begin(), expected_barriers.end(), frame.barrier_id) ==
                    expected_barriers.end()) {
                frame_structure_valid = false;
                append_mismatch(report, frame.window_index, 0, frame.barrier_id,
                                "frame_structure", "frame_identity", "unexpected_frame",
                                "declared_window_and_barrier", std::string(lane_name));
            }
        }
        for (std::size_t window = 0; window < trace.windows.size(); ++window) {
            for (const auto &barrier_id : expected_barriers) {
                const std::size_t count = count_frames(lane, window, barrier_id);
                if (count != 1) {
                    frame_structure_valid = false;
                    append_mismatch(report, window, 0, barrier_id, "frame_structure",
                                    "frame_identity", count == 0 ? "missing_frame"
                                                                 : "duplicate_frame",
                                    "exactly_one", std::to_string(count));
                }
            }
            const ReplayLaneFrame *window_frame =
                find_unique_frame(lane, window, "window_commit");
            const ReplayLaneFrame *export_frame = find_unique_frame(lane, window, "export");
            if (window_frame != nullptr && export_frame != nullptr &&
                window_frame->source_snapshot_version != export_frame->source_snapshot_version) {
                frame_structure_valid = false;
                append_mismatch(report, window, 0, "export", "frame_structure",
                                "source_snapshot_version", "lane_snapshot_mismatch",
                                std::to_string(window_frame->source_snapshot_version),
                                std::to_string(export_frame->source_snapshot_version));
            }
        }
    };
    validate_lane_frames(reference, "reference");
    validate_lane_frames(shadow, "shadow");

    for (std::size_t window = 0; window < trace.windows.size(); ++window) {
        for (const std::string_view barrier_id : {std::string_view("window_commit"),
                                                  std::string_view("export")}) {
            const ReplayLaneFrame *reference_frame =
                find_unique_frame(reference, window, barrier_id);
            const ReplayLaneFrame *shadow_frame = find_unique_frame(shadow, window, barrier_id);
            if (reference_frame == nullptr || shadow_frame == nullptr) continue;
            report.reference_source_snapshot_versions.push_back(
                reference_frame->source_snapshot_version);
            report.shadow_source_snapshot_versions.push_back(shadow_frame->source_snapshot_version);
            if (reference_frame->source_snapshot_version != shadow_frame->source_snapshot_version) {
                frame_structure_valid = false;
                append_mismatch(report, window, 0, barrier_id, "frame_structure",
                                "source_snapshot_version", "source_snapshot_mismatch",
                                std::to_string(reference_frame->source_snapshot_version),
                                std::to_string(shadow_frame->source_snapshot_version));
            }
        }
    }

    for (const auto &family : budget->selected_slice_fields) {
        append_unique(report.coverage.consumed_field_families, family.field_family);
        report.coverage.consumed_selected_field_count += family.selected_fields.size();
        for (const auto &barrier_id : family.comparison_barriers) {
            const auto *rule = find_barrier_rule(barrier_id);
            if (rule == nullptr || !rule->enabled || !rule->comparison_eligible) {
                append_mismatch(report, 0, 0, barrier_id, family.field_family, "<barrier>",
                                "invalid_comparison_barrier", "enabled_comparison_barrier",
                                "disabled_or_missing");
                continue;
            }
            append_unique(report.coverage.consumed_barriers, barrier_id);
            for (std::size_t window = 0; window < trace.windows.size(); ++window) {
                const ReplayLaneFrame *reference_frame =
                    find_unique_frame(reference, window, barrier_id);
                const ReplayLaneFrame *shadow_frame =
                    find_unique_frame(shadow, window, barrier_id);
                for (std::size_t world = 0; world < trace.seeds.size(); ++world) {
                    for (const auto &selected : family.selected_fields) {
                        ++report.coverage.selected_field_instances;
                        const std::size_t reference_count =
                            count_fields(reference_frame, world, family.field_family,
                                         selected.field_path);
                        const std::size_t shadow_count =
                            count_fields(shadow_frame, world, family.field_family,
                                         selected.field_path);
                        const ReplayFieldValue *reference_value =
                            find_unique_field(reference_frame, world, family.field_family,
                                              selected.field_path);
                        const ReplayFieldValue *shadow_value =
                            find_unique_field(shadow_frame, world, family.field_family,
                                              selected.field_path);
                        if (reference_value == nullptr || shadow_value == nullptr ||
                            !reference_value->available || !shadow_value->available) {
                            ++report.coverage.unavailable_field_instances;
                            const std::string code =
                                reference_count > 1 || shadow_count > 1 ? "duplicate_field"
                                                                        : "field_unavailable";
                            append_mismatch(
                                report, window, world, barrier_id, family.field_family,
                                selected.field_path, code,
                                reference_value == nullptr ? "<missing>"
                                                           : reference_value->canonical_value,
                                shadow_value == nullptr ? "<missing>"
                                                        : shadow_value->canonical_value);
                            continue;
                        }
                        if (reference_value->value_kind != selected.value_kind ||
                            shadow_value->value_kind != selected.value_kind) {
                            ++report.coverage.unavailable_field_instances;
                            append_mismatch(report, window, world, barrier_id,
                                            family.field_family, selected.field_path,
                                            "value_kind_mismatch", "frozen_value_kind",
                                            "lane_value_kind");
                            continue;
                        }
                        ++report.coverage.available_field_instances;
                        if (values_match(family, *reference_value, *shadow_value)) {
                            ++report.coverage.matched_field_instances;
                        } else {
                            ++report.coverage.mismatched_field_instances;
                            append_mismatch(report, window, world, barrier_id, family.field_family,
                                            selected.field_path, "value_mismatch",
                                            reference_value->canonical_value,
                                            shadow_value->canonical_value);
                        }
                    }
                }
            }
        }
    }

    report.complete_selected_slice =
        frame_structure_valid &&
        report.coverage.consumed_field_families.size() == budget->selected_slice_fields.size() &&
        report.coverage.consumed_selected_field_count ==
            report.coverage.expected_selected_field_count &&
        report.coverage.selected_field_instances == report.coverage.expected_field_instances &&
        report.coverage.available_field_instances == report.coverage.expected_field_instances &&
        report.coverage.unavailable_field_instances == 0 &&
        report.coverage.consumed_barriers.size() == report.coverage.expected_barrier_count;
    report.quarantined = !report.complete_selected_slice || !report.mismatches.empty();
    report.status = !report.complete_selected_slice
                        ? ReplayRunStatus::rejected
                        : (report.quarantined ? ReplayRunStatus::quarantined
                                              : ReplayRunStatus::passed);
    report.rejection_reason = !report.complete_selected_slice
                                  ? "incomplete_selected_slice"
                                  : (report.quarantined ? "parity_mismatch" : "");
    if (const auto *first = report.first_divergence(); first != nullptr) {
        report.sync_barrier_id = first->barrier_id;
        report.mismatch_domain = first->field_family;
        report.mismatch_summary = first->mismatch_code + ":" + first->field_path;
    } else {
        report.sync_barrier_id = "none";
        report.mismatch_domain = "none";
        report.mismatch_summary = "selected_slice_matched";
    }
    report.stable_signature = build_stable_signature(report);
    return report;
}

ReplayComparisonReport CudaResidentReplayHarness::rerun(
    const ReplayTrace &trace, const ReplayComparisonReport &prior) const {
    const std::string requested_trace_signature = trace_signature(trace);
    if (prior.run_id != trace.run_id || prior.backend_profile_id != trace.backend_profile_id ||
        prior.parity_budget_ref != trace.parity_budget_ref ||
        prior.trace_signature != requested_trace_signature) {
        ReplayComparisonReport rejected = prior;
        rejected.status = ReplayRunStatus::rejected;
        rejected.rejection_reason = "rerun_trace_identity_mismatch";
        rejected.deterministic = false;
        rejected.quarantined = true;
        rejected.candidate_promotion_blocked = true;
        append_mismatch(rejected, 0, 0, "input_injection", "diagnostics_trace",
                        "trace_signature", "rerun_trace_identity_mismatch", prior.trace_signature,
                        requested_trace_signature);
        rejected.mismatch_domain = "diagnostics_trace";
        rejected.sync_barrier_id = "input_injection";
        rejected.mismatch_summary = "rerun_trace_identity_mismatch:trace_signature";
        rejected.stable_signature = build_stable_signature(rejected);
        return rejected;
    }
    ReplayComparisonReport rerun_report = run(trace);
    rerun_report.deterministic = rerun_report.stable_signature == prior.stable_signature;
    if (!rerun_report.deterministic) {
        append_mismatch(rerun_report, 0, 0, "export", "diagnostics_trace", "stable_signature",
                        "nondeterministic_rerun", prior.stable_signature,
                        rerun_report.stable_signature);
        rerun_report.quarantined = true;
        rerun_report.candidate_promotion_blocked = true;
        rerun_report.status = ReplayRunStatus::quarantined;
        rerun_report.rejection_reason = "nondeterministic_rerun";
        rerun_report.mismatch_domain = "diagnostics_trace";
        rerun_report.sync_barrier_id = "export";
        rerun_report.mismatch_summary = "nondeterministic_rerun:stable_signature";
        rerun_report.stable_signature = build_stable_signature(rerun_report);
    }
    return rerun_report;
}

} // namespace runtime::cuda_resident::replay
