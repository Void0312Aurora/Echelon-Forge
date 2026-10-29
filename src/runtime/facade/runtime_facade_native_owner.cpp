#include "runtime/facade/runtime_facade_types.h"

#include "core/engine/simulation_kernel.h"
#include "core/engine/simulation_kernel_command_surface.h"
#include "runtime/crypto/sha256.h"
#include "runtime/contracts/composition/resolved_execution_plan.v1.generated.h"
#include "runtime/contracts/native_world_state_codec.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <memory>
#include <nlohmann/json.hpp>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

bool lower_hex_sha256(const std::string &value) {
    if (value.size() != 64) {
        return false;
    }
    return std::all_of(value.begin(), value.end(), [](unsigned char character) {
        return std::isdigit(character) != 0 || (character >= 'a' && character <= 'f');
    });
}

bool valid_pilot_action(const PilotAction &action) {
    const auto in_range = [](double value, double minimum, double maximum) {
        return std::isfinite(value) && value >= minimum && value <= maximum;
    };
    return action.active && in_range(action.stick_pitch, -1.0, 1.0) &&
           in_range(action.stick_roll, -1.0, 1.0) && in_range(action.rudder, -1.0, 1.0) &&
           in_range(action.throttle, 0.0, 1.0) && in_range(action.gear_handle, 0.0, 1.0) &&
           in_range(action.flaps, 0.0, 1.0) && in_range(action.speedbrake, 0.0, 1.0) &&
           in_range(action.brake, 0.0, 1.0) && std::isfinite(action.radar_scan_az) &&
           std::isfinite(action.radar_scan_el) && action.weapon_select_id >= 0 &&
           action.jammer_mode >= -1 && action.jammer_mode <= 2;
}

std::vector<std::uint8_t> bytes(const std::string &value) {
    return {value.begin(), value.end()};
}

RuntimeNativeSnapshotFacts snapshot_for(SimulationKernel &kernel, std::uint64_t step) {
    const std::string world = runtime::contracts::serialize_native_world_state(kernel);
    const std::string rng = runtime::contracts::serialize_native_rng_state(kernel);
    return {
        .step = step,
        .state_digest = runtime::crypto::sha256_hex(world),
        .event_cursor = step,
        .rng_digest = runtime::crypto::sha256_hex(rng),
        .terminated = false,
    };
}

using EntityRemap = std::unordered_map<std::uint64_t, std::uint64_t>;

struct ClonedKernel {
    std::shared_ptr<SimulationKernel> kernel;
    // Source-local entity ids to target-local entity ids.  The public branch
    // keeps its source ids as stable handles and composes this map at every
    // checkpoint/fork boundary.
    EntityRemap local_entity_remap;
};

ClonedKernel clone_kernel(SimulationKernel &source, std::uint64_t step) {
    std::unordered_map<std::string, std::uint64_t> source_ids_by_name;
    {
        auto lease = source.acquire_world_lease();
        lease.world().query<SimObject>().each([&](flecs::entity entity, const SimObject &) {
            std::string name = entity.name() != nullptr ? entity.name() : "";
            if (name.empty() || name.starts_with('#')) {
                name = "p4b-simobject-" + std::to_string(entity.id());
            }
            source_ids_by_name.emplace(std::move(name), static_cast<std::uint64_t>(entity.id()));
        });
    }
    const std::string world = runtime::contracts::serialize_native_world_state(source);
    const std::string rng = runtime::contracts::serialize_native_rng_state(source);
    // The native codec requires a nonzero barrier sequence even for the
    // initial step-zero snapshot. This branch barrier is local to the child;
    // it does not claim a candidate-host episode barrier.
    const std::string clock =
        runtime::contracts::serialize_native_clock_state(source, step, step + 1);

    // WorldBatchRuntime uses the generated default plan for maintained CPU
    // worlds. The state owner restores the complete reflected ECS state, RNG,
    // and clock into this independent kernel before the child is exposed.
    auto child = std::make_shared<SimulationKernel>(
        std::string(runtime::contracts::generated::kDefaultResolvedExecutionPlanJson));
    if (!runtime::contracts::restore_native_world_state(*child, bytes(world))) {
        throw std::runtime_error("native child branch could not restore world state");
    }
    if (!runtime::contracts::restore_native_rng_state(*child, bytes(rng))) {
        throw std::runtime_error("native child branch could not restore RNG state");
    }
    if (!runtime::contracts::restore_native_clock_state(*child, bytes(clock))) {
        throw std::runtime_error("native child branch could not restore clock state");
    }

    const auto document = nlohmann::json::parse(world);
    if (!document.contains("results") || !document.at("results").is_array()) {
        throw std::runtime_error("native child branch world state has no entity identities");
    }
    EntityRemap remap;
    remap.reserve(document.at("results").size());
    auto lease = child->acquire_world_lease();
    for (const auto &result : document.at("results")) {
        if (!result.is_object() || !result.contains("name") || !result.at("name").is_string()) {
            throw std::runtime_error("native child branch entity identity is malformed: " +
                                     result.dump());
        }
        const auto name = result.at("name").get_ref<const std::string &>();
        const auto source_id = source_ids_by_name.find(name);
        if (source_id == source_ids_by_name.end()) {
            throw std::runtime_error("native child branch entity identity has no source owner: " +
                                     name);
        }
        const auto entity = lease.world().lookup(name.c_str());
        if (!entity.is_valid() || !entity.is_alive() || !entity.has<SimObject>() ||
            !remap.emplace(source_id->second, static_cast<std::uint64_t>(entity.id())).second) {
            throw std::runtime_error("native child branch entity identity was not restored");
        }
    }
    return {.kernel = std::move(child), .local_entity_remap = std::move(remap)};
}

std::optional<std::uint64_t> translate_entity(const EntityRemap &remap, std::uint64_t external_id) {
    const auto found = remap.find(external_id);
    return found == remap.end() ? std::nullopt : std::optional<std::uint64_t>(found->second);
}

EntityRemap compose_remap(const EntityRemap &external_to_source,
                          const EntityRemap &source_to_target) {
    EntityRemap result;
    result.reserve(external_to_source.size());
    for (const auto &[external_id, source_id] : external_to_source) {
        const auto target = source_to_target.find(source_id);
        if (target == source_to_target.end()) {
            throw std::runtime_error("native child branch lost an entity identity");
        }
        result.emplace(external_id, target->second);
    }
    return result;
}

} // namespace

bool RuntimeNativeSnapshotFacts::well_formed() const noexcept {
    return lower_hex_sha256(state_digest) && lower_hex_sha256(rng_digest) && event_cursor == step;
}

struct RuntimeFacadeNativeBranch::State {
    std::shared_ptr<SimulationKernel> kernel;
    std::uint64_t step = 0;
    std::uint64_t remaining_steps = 0;
    std::string intervention_digest;
    EntityRemap entity_remap;
    bool valid = false;
};

RuntimeFacadeNativeBranch::RuntimeFacadeNativeBranch(std::shared_ptr<State> state) noexcept
    : state_(std::move(state)) {}

RuntimeFacadeNativeBranch::RuntimeFacadeNativeBranch(RuntimeFacadeNativeBranch &&) noexcept =
    default;
RuntimeFacadeNativeBranch &
RuntimeFacadeNativeBranch::operator=(RuntimeFacadeNativeBranch &&) noexcept = default;
RuntimeFacadeNativeBranch::~RuntimeFacadeNativeBranch() = default;

bool RuntimeFacadeNativeBranch::valid() const noexcept {
    return state_ != nullptr && state_->valid && state_->kernel != nullptr;
}

RuntimeNativeSnapshotFacts RuntimeFacadeNativeBranch::snapshot_facts() const {
    if (!valid()) {
        return {};
    }
    try {
        return snapshot_for(*state_->kernel, state_->step);
    } catch (...) {
        return {};
    }
}

bool RuntimeFacadeNativeBranch::step_pilot_actions(
    const std::vector<WorldPilotActionAssignment> &actions) {
    if (!valid() || state_->remaining_steps == 0 || actions.size() > 64) {
        return false;
    }
    try {
        std::vector<std::pair<std::uint64_t, const PilotAction *>> translated;
        translated.reserve(actions.size());
        std::set<std::uint64_t> target_ids;
        for (const auto &assignment : actions) {
            if (assignment.world_index != 0 || assignment.entity_id == 0 ||
                !valid_pilot_action(assignment.action)) {
                return false;
            }
            const auto entity_id = translate_entity(state_->entity_remap, assignment.entity_id);
            if (!entity_id.has_value() || !target_ids.insert(*entity_id).second) {
                return false;
            }
            translated.emplace_back(*entity_id, &assignment.action);
        }
        {
            auto lease = state_->kernel->acquire_world_lease();
            for (const auto &[entity_id, _action] : translated) {
                const auto entity = lease.world().entity(entity_id);
                if (!entity.is_valid() || !entity.is_alive() || !entity.has<SimObject>() ||
                    entity.get<Transform>() == nullptr || entity.get<Velocity>() == nullptr) {
                    return false;
                }
            }
        }
        SimulationKernelCommandSurface commands(*state_->kernel);
        for (const auto &[entity_id, action] : translated) {
            commands.set_pilot_action(entity_id, *action);
        }
        state_->kernel->step();
    } catch (...) {
        return false;
    }
    ++state_->step;
    --state_->remaining_steps;
    return true;
}

ObservationBatchPacket
RuntimeFacadeNativeBranch::read_observation_packet(const std::vector<WorldEntityRef> &refs) const {
    ObservationBatchPacket packet{};
    packet.refs = refs;
    packet.barrier_id = "export";
    packet.snapshot_version = state_ != nullptr ? state_->step + 1 : 0;
    if (!valid()) {
        return packet;
    }
    try {
        packet.provenance.information_state_layer =
            std::string(kPolicyInformationStateAgentObservation);
        packet.provenance.source_label = std::string(kPolicySourceLabelFacadeObservationPacket);
        packet.provenance.maintained_status = std::string(kPolicyMaintainedStatusMaintained);
        packet.provenance.observation_packet_ids = {"obs:facade-native-branch:" +
                                                    std::to_string(packet.snapshot_version)};
        packet.provenance.source_observation_versions = {"branch:" +
                                                         std::to_string(packet.snapshot_version)};
        for (const auto &ref : refs) {
            if (ref.world_index != 0 || ref.entity_id == 0) {
                return {};
            }
            const auto entity_id = translate_entity(state_->entity_remap, ref.entity_id);
            if (!entity_id.has_value()) {
                return {};
            }
            auto lease = state_->kernel->acquire_world_lease();
            auto entity = lease.world().entity(*entity_id);
            if (!entity.is_valid() || !entity.is_alive() || !entity.get<Transform>() ||
                !entity.get<Velocity>()) {
                return {};
            }
            auto observation = state_->kernel->get_agent_observation(*entity_id);
            // Keep the caller's logical handle stable across a native restore;
            // the child-local Flecs id is an implementation detail.
            observation.id = ref.entity_id;
            packet.agent_observations.push_back(std::move(observation));
        }
        if (!packet.agent_observations.empty()) {
            packet.source_time_s = packet.agent_observations.front().sim_time;
        }
        return packet;
    } catch (...) {
        return {};
    }
}

std::unique_ptr<RuntimeFacadeNativeBranch> RuntimeFacadeNativeBranch::checkpoint() const {
    if (!valid()) {
        return {};
    }
    try {
        auto cloned = clone_kernel(*state_->kernel, state_->step);
        auto child_state = std::make_shared<State>();
        child_state->kernel = std::move(cloned.kernel);
        child_state->step = state_->step;
        child_state->remaining_steps = state_->remaining_steps;
        child_state->intervention_digest = state_->intervention_digest;
        child_state->entity_remap = compose_remap(state_->entity_remap, cloned.local_entity_remap);
        child_state->valid = true;
        return std::unique_ptr<RuntimeFacadeNativeBranch>(
            new RuntimeFacadeNativeBranch(std::move(child_state)));
    } catch (...) {
        return {};
    }
}

std::unique_ptr<RuntimeFacadeNativeBranch>
RuntimeFacadeNativeBranch::fork_native_branch(std::string intervention_digest,
                                              std::uint64_t horizon) const {
    if (!valid() || horizon == 0 || !lower_hex_sha256(intervention_digest)) {
        return {};
    }
    auto child = checkpoint();
    if (child == nullptr) {
        return {};
    }
    child->state_->remaining_steps = horizon;
    child->state_->intervention_digest = std::move(intervention_digest);
    return child;
}

// Kept in this translation unit so the PIMPL remains opaque at the public
// facade boundary. FlecsCpuBackend is the only constructor of a branch.
std::unique_ptr<RuntimeFacadeNativeBranch>
make_runtime_facade_native_branch(SimulationKernel &source, std::uint64_t step,
                                  std::string intervention_digest, std::uint64_t horizon) {
    if (horizon == 0 || !lower_hex_sha256(intervention_digest)) {
        return {};
    }
    auto cloned = clone_kernel(source, step);
    auto state = std::make_shared<RuntimeFacadeNativeBranch::State>();
    state->kernel = std::move(cloned.kernel);
    state->step = step;
    state->remaining_steps = horizon;
    state->intervention_digest = std::move(intervention_digest);
    state->entity_remap = std::move(cloned.local_entity_remap);
    state->valid = true;
    return std::unique_ptr<RuntimeFacadeNativeBranch>(
        new RuntimeFacadeNativeBranch(std::move(state)));
}
