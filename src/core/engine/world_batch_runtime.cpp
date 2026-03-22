#include "core/engine/world_batch_runtime.h"

#include <algorithm>
#include <atomic>
#include <cmath>
#include <exception>
#include <mutex>
#include <stdexcept>
#include <thread>

namespace {

size_t hardware_thread_count() noexcept {
    const unsigned int hc = std::thread::hardware_concurrency();
    return hc == 0U ? 1U : static_cast<size_t>(hc);
}

template <typename Fn>
void parallel_for_index(size_t task_count, size_t requested_threads, Fn&& fn) {
    if (task_count == 0) {
        return;
    }
    const size_t thread_count = std::min(
        task_count,
        requested_threads == 0 ? hardware_thread_count() : std::max<size_t>(1, requested_threads)
    );
    if (thread_count <= 1) {
        for (size_t i = 0; i < task_count; ++i) {
            fn(i);
        }
        return;
    }

    const size_t chunk_size = (task_count + thread_count - 1) / thread_count;
    std::vector<std::thread> workers;
    workers.reserve(thread_count - 1);

    std::exception_ptr first_exception;
    std::mutex exception_mutex;

    auto run_range = [&](size_t begin, size_t end) {
        for (size_t i = begin; i < end; ++i) {
            try {
                fn(i);
            } catch (...) {
                std::lock_guard<std::mutex> lock(exception_mutex);
                if (first_exception == nullptr) {
                    first_exception = std::current_exception();
                }
                break;
            }
        }
    };

    size_t begin = 0;
    for (size_t worker_idx = 1; worker_idx < thread_count; ++worker_idx) {
        const size_t end = std::min(task_count, begin + chunk_size);
        workers.emplace_back(run_range, begin, end);
        begin = end;
    }
    run_range(begin, task_count);
    for (auto& worker : workers) {
        worker.join();
    }
    if (first_exception != nullptr) {
        std::rethrow_exception(first_exception);
    }
}

template <typename Item>
std::vector<std::vector<size_t>> group_item_indices_by_world(size_t world_count, const std::vector<Item>& items) {
    std::vector<std::vector<size_t>> grouped(world_count);
    for (size_t item_index = 0; item_index < items.size(); ++item_index) {
        const size_t world_index = static_cast<size_t>(items[item_index].world_index);
        if (world_index >= world_count) {
            throw std::out_of_range("world index out of range");
        }
        grouped[world_index].push_back(item_index);
    }
    return grouped;
}

}  // namespace

WorldBatchRuntime::WorldBatchRuntime(size_t world_count) {
    resize(world_count);
}

void WorldBatchRuntime::resize(size_t world_count) {
    worlds_.clear();
    worlds_.reserve(world_count);
    for (size_t i = 0; i < world_count; ++i) {
        worlds_.push_back(std::make_unique<SimulationKernel>());
    }
}

SimulationKernel& WorldBatchRuntime::checked_world(size_t index) {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

const SimulationKernel& WorldBatchRuntime::checked_world(size_t index) const {
    if (index >= worlds_.size()) {
        throw std::out_of_range("world index out of range");
    }
    return *worlds_[index];
}

SimulationKernel& WorldBatchRuntime::world(size_t index) {
    return checked_world(index);
}

const SimulationKernel& WorldBatchRuntime::world(size_t index) const {
    return checked_world(index);
}

size_t WorldBatchRuntime::resolve_worker_threads(size_t task_count) const noexcept {
    if (task_count == 0) {
        return 1;
    }
    const size_t configured = worker_threads_ == 0 ? hardware_thread_count() : std::max<size_t>(1, worker_threads_);
    return std::min(task_count, configured);
}

size_t WorldBatchRuntime::effective_worker_threads() const noexcept {
    return resolve_worker_threads(worlds_.size());
}

void WorldBatchRuntime::reset_batch(const std::vector<uint32_t>& seeds) {
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        uint32_t seed = static_cast<uint32_t>(42 + i);
        if (seeds.size() == worlds_.size()) {
            seed = seeds[i];
        } else if (seeds.size() == 1) {
            seed = static_cast<uint32_t>(seeds[0] + static_cast<uint32_t>(i));
        }
        worlds_[i]->reset(seed);
    });
}

void WorldBatchRuntime::step_batch() {
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        worlds_[i]->step();
    });
}

void WorldBatchRuntime::step_worlds(const std::vector<uint64_t>& world_indices) {
    if (world_indices.empty()) {
        return;
    }
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).step();
    });
}

bool WorldBatchRuntime::load_database(const std::string& path) {
    std::atomic<bool> ok{true};
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        if (!worlds_[i]->load_database(path)) {
            ok.store(false, std::memory_order_relaxed);
        }
    });
    return ok.load(std::memory_order_relaxed);
}

bool WorldBatchRuntime::load_unit_definitions(const std::string& path, std::string* error) {
    std::atomic<bool> ok{true};
    std::string first_error;
    std::mutex error_mutex;
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        std::string local_error;
        const bool local_ok = worlds_[i]->load_unit_definitions(path, &local_error);
        if (!local_ok) {
            ok.store(false, std::memory_order_relaxed);
            if (!local_error.empty()) {
                std::lock_guard<std::mutex> lock(error_mutex);
                if (first_error.empty()) {
                    first_error = local_error;
                }
            }
        }
    });
    if (error != nullptr) {
        *error = first_error;
    }
    return ok.load(std::memory_order_relaxed);
}

void WorldBatchRuntime::set_time_step(double dt) {
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
        worlds_[i]->set_time_step(dt);
    });
}

void WorldBatchRuntime::set_terrain_types_batch(const std::vector<WorldTerrainAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            world.set_terrain_type(assignments[item_index].terrain_type);
        }
    });
}

void WorldBatchRuntime::set_winds_batch(const std::vector<WorldWindAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_wind(item.speed_mps, item.dir_from_deg, item.shear_mps_per_km);
        }
    });
}

void WorldBatchRuntime::clear_zones_batch(const std::vector<uint64_t>& world_indices) {
    if (world_indices.empty()) {
        parallel_for_index(worlds_.size(), worker_threads_, [&](size_t i) {
            worlds_[i]->clear_zones();
        });
        return;
    }
    parallel_for_index(world_indices.size(), worker_threads_, [&](size_t i) {
        checked_world(static_cast<size_t>(world_indices[i])).clear_zones();
    });
}

void WorldBatchRuntime::add_zones_batch(const std::vector<WorldZoneDefinition>& zones) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), zones);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& zone = zones[item_index];
            world.add_zone(zone.name, zone.x, zone.y, zone.width, zone.length, zone.heading, zone.surface_type);
        }
    });
}

std::vector<uint64_t> WorldBatchRuntime::spawn_units_batch(const std::vector<WorldSpawnRequest>& requests) {
    std::vector<uint64_t> out(requests.size(), 0);
    const auto grouped = group_item_indices_by_world(worlds_.size(), requests);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = requests[item_index];
            const auto entity = world.spawn_unit(
                item.side,
                item.type_name,
                item.x,
                item.y,
                item.z,
                item.heading,
                item.pitch,
                item.roll,
                item.vx,
                item.vy,
                item.vz
            );
            out[item_index] = entity.id();
        }
    });
    return out;
}

std::vector<uint64_t> WorldBatchRuntime::apply_world_setup_batch(
    const std::vector<uint32_t>& seeds,
    const std::vector<WorldTerrainAssignment>& terrain_assignments,
    const std::vector<WorldWindAssignment>& wind_assignments,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<WorldSpawnRequest>& requests,
    const std::vector<double>& time_steps
) {
    if (!time_steps.empty() && time_steps.size() != 1 && time_steps.size() != worlds_.size()) {
        throw std::invalid_argument("time_steps must have size 0, 1, or world_count");
    }

    std::vector<uint64_t> out(requests.size(), 0);
    const auto terrain_grouped = group_item_indices_by_world(worlds_.size(), terrain_assignments);
    const auto wind_grouped = group_item_indices_by_world(worlds_.size(), wind_assignments);
    const auto zone_grouped = group_item_indices_by_world(worlds_.size(), zones);
    const auto spawn_grouped = group_item_indices_by_world(worlds_.size(), requests);

    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);

        if (!time_steps.empty()) {
            const double dt = time_steps.size() == 1 ? time_steps[0] : time_steps[world_index];
            if (std::isfinite(dt) && dt > 0.0) {
                world.set_time_step(dt);
            }
        }

        for (const size_t item_index : terrain_grouped[world_index]) {
            world.set_terrain_type(terrain_assignments[item_index].terrain_type);
        }
        for (const size_t item_index : wind_grouped[world_index]) {
            const auto& item = wind_assignments[item_index];
            world.set_wind(item.speed_mps, item.dir_from_deg, item.shear_mps_per_km);
        }

        world.clear_zones();
        for (const size_t item_index : zone_grouped[world_index]) {
            const auto& zone = zones[item_index];
            world.add_zone(zone.name, zone.x, zone.y, zone.width, zone.length, zone.heading, zone.surface_type);
        }

        uint32_t seed = static_cast<uint32_t>(42 + world_index);
        if (seeds.size() == worlds_.size()) {
            seed = seeds[world_index];
        } else if (seeds.size() == 1) {
            seed = static_cast<uint32_t>(seeds[0] + static_cast<uint32_t>(world_index));
        }
        world.reset(seed);

        for (const size_t item_index : spawn_grouped[world_index]) {
            const auto& item = requests[item_index];
            const auto entity = world.spawn_unit(
                item.side,
                item.type_name,
                item.x,
                item.y,
                item.z,
                item.heading,
                item.pitch,
                item.roll,
                item.vx,
                item.vy,
                item.vz
            );
            out[item_index] = entity.id();
        }
    });
    return out;
}

void WorldBatchRuntime::set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_pilot_action(item.entity_id, item.action);
        }
    });
}

void WorldBatchRuntime::set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_mission_command(item.entity_id, item.command);
        }
    });
}

void WorldBatchRuntime::set_task_orders_batch(const std::vector<WorldTaskOrderAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_task_order(item.entity_id, item.order);
        }
    });
}

void WorldBatchRuntime::set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_leader_intent(item.entity_id, item.intent);
        }
    });
}

void WorldBatchRuntime::set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment>& assignments) {
    const auto grouped = group_item_indices_by_world(worlds_.size(), assignments);
    parallel_for_index(worlds_.size(), worker_threads_, [&](size_t world_index) {
        auto& world = checked_world(world_index);
        for (const size_t item_index : grouped[world_index]) {
            const auto& item = assignments[item_index];
            world.set_pilot_report(item.entity_id, item.report);
        }
    });
}

std::vector<AgentObservation> WorldBatchRuntime::get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<AgentObservation> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_agent_observation(ref.entity_id);
    });
    return out;
}

InstrumentState WorldBatchRuntime::safe_get_instrument_state(const SimulationKernel& world, uint64_t entity_id) {
    auto e = world.get_world().entity(entity_id);
    if (e.is_valid()) {
        const InstrumentState* inst = e.get<InstrumentState>();
        if (inst != nullptr) {
            return *inst;
        }
    }
    return InstrumentState{};
}

std::vector<InstrumentState> WorldBatchRuntime::get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<InstrumentState> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = safe_get_instrument_state(checked_world(static_cast<size_t>(ref.world_index)), ref.entity_id);
    });
    return out;
}

std::vector<MissionCommand> WorldBatchRuntime::get_mission_commands_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<MissionCommand> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_mission_command(ref.entity_id);
    });
    return out;
}

std::vector<TaskOrder> WorldBatchRuntime::get_task_orders_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<TaskOrder> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_task_order(ref.entity_id);
    });
    return out;
}

std::vector<LeaderIntent> WorldBatchRuntime::get_leader_intents_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<LeaderIntent> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_leader_intent(ref.entity_id);
    });
    return out;
}

std::vector<PilotReport> WorldBatchRuntime::get_pilot_reports_batch(const std::vector<WorldEntityRef>& refs) const {
    std::vector<PilotReport> out(refs.size());
    parallel_for_index(refs.size(), worker_threads_, [&](size_t i) {
        const auto& ref = refs[i];
        out[i] = checked_world(static_cast<size_t>(ref.world_index)).get_pilot_report(ref.entity_id);
    });
    return out;
}
