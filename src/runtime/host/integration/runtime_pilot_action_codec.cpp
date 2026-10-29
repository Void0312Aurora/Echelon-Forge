#include "runtime_pilot_action_codec.h"

#include "components/basic/common.h"
#include "components/basic/tags.h"
#include "runtime/contracts/authority/runtime_authority_contract.h"

#include <cmath>
#include <set>
#include <string>
#include <nlohmann/json.hpp>

namespace runtime::host::integration {
namespace {

// Keep every maintained PilotAction field in the transport, including explicit
// default jammer semantics. Unknown/missing fields fail the closed schema.
// clang-format off
#define PILOT_FIELDS(X) \
    X(stick_pitch) \
    X(stick_roll) \
    X(rudder) \
    X(throttle) \
    X(gear_handle) \
    X(flaps) \
    X(speedbrake) \
    X(brake) \
    X(brake_left) \
    X(brake_right) \
    X(radar_active) \
    X(radar_scan_az) \
    X(radar_scan_el) \
    X(tms_up) \
    X(master_arm) \
    X(fire_weapon) \
    X(fire_gun) \
    X(weapon_select_id) \
    X(jettison_emergency) \
    X(program_chaff) \
    X(program_flare) \
    X(jammer_transmit) \
    X(jammer_mode) \
    X(active)
// clang-format on

bool valid_action(const PilotAction &a) {
    const auto range = [](double value, double low, double high) {
        return std::isfinite(value) && value >= low && value <= high;
    };
    return a.active && range(a.stick_pitch, -1, 1) && range(a.stick_roll, -1, 1) &&
           range(a.rudder, -1, 1) && range(a.throttle, 0, 1) && range(a.gear_handle, 0, 1) &&
           range(a.flaps, 0, 1) && range(a.speedbrake, 0, 1) && range(a.brake, 0, 1) &&
           std::isfinite(a.radar_scan_az) && std::isfinite(a.radar_scan_el) &&
           a.weapon_select_id >= 0 && a.jammer_mode >= -1 && a.jammer_mode <= 2;
}

nlohmann::json action_json(const PilotAction &a) {
    nlohmann::json j = nlohmann::json::object();
#define WRITE_FIELD(field) j[#field] = a.field;
    PILOT_FIELDS(WRITE_FIELD)
#undef WRITE_FIELD
    return j;
}

} // namespace

std::optional<std::vector<std::uint8_t>>
encode_pilot_actions(const std::vector<WorldPilotActionAssignment> &actions) {
    if (actions.empty() || actions.size() > 64) return std::nullopt;
    std::set<std::uint64_t> ids;
    auto rows = nlohmann::json::array();
    for (const auto &assignment : actions) {
        if (assignment.world_index != 0 || assignment.entity_id == 0 ||
            !ids.insert(assignment.entity_id).second || !valid_action(assignment.action)) {
            return std::nullopt;
        }
        rows.push_back({{"world_index", 0},
                        {"entity_id", assignment.entity_id},
                        {"action", action_json(assignment.action)}});
    }
    const auto canonical = runtime::authority_contracts::canonical_authority_json(nlohmann::json{
        {"schema", "echelon_forge.runtime_pilot_actions.v1"}, {"assignments", rows}}.dump());
    if (!canonical || canonical->size() > 65536) return std::nullopt;
    return std::vector<std::uint8_t>(canonical->begin(), canonical->end());
}

std::optional<std::vector<WorldPilotActionAssignment>>
decode_pilot_actions(const std::vector<std::uint8_t> &payload) {
    if (payload.empty() || payload.size() > 65536) return std::nullopt;
    try {
        const auto j = nlohmann::json::parse(payload.begin(), payload.end());
        if (j.size() != 2 || j.at("schema") != "echelon_forge.runtime_pilot_actions.v1" ||
            !j.at("assignments").is_array())
            return std::nullopt;
        std::vector<WorldPilotActionAssignment> actions;
        for (const auto &row : j.at("assignments")) {
            if (row.size() != 3 || !row.at("entity_id").is_number_unsigned() ||
                !row.at("world_index").is_number_unsigned())
                return std::nullopt;
            WorldPilotActionAssignment assignment{};
            assignment.world_index = row.at("world_index").get<std::uint64_t>();
            assignment.entity_id = row.at("entity_id").get<std::uint64_t>();
            const auto &action = row.at("action");
#define READ_FIELD(field)                                                                          \
    assignment.action.field = action.at(#field).get<decltype(assignment.action.field)>();
            PILOT_FIELDS(READ_FIELD)
#undef READ_FIELD
            if (action.size() != action_json(assignment.action).size()) return std::nullopt;
            actions.push_back(assignment);
        }
        // Reject coercions, duplicate keys, alternate encodings, and noncanonical
        // number forms rather than silently changing the committed command.
        if (encode_pilot_actions(actions) != std::optional{payload}) return std::nullopt;
        return actions;
    } catch (...) {
        return std::nullopt;
    }
}

bool pilot_action_entities_valid(SimulationKernel &kernel,
                                 const std::vector<WorldPilotActionAssignment> &actions) {
    auto lease = kernel.acquire_world_lease();
    for (const auto &assignment : actions) {
        const auto entity = lease.world().entity(assignment.entity_id);
        if (!entity.is_valid() || !entity.is_alive() || !entity.has<SimObject>() ||
            entity.get<Transform>() == nullptr || entity.get<Velocity>() == nullptr)
            return false;
    }
    return true;
}

std::uint64_t resolve_pilot_entity(SimulationKernel &kernel, std::string_view logical_name) {
    if (logical_name.empty() || logical_name.find('\0') != std::string_view::npos) return 0;
    auto lease = kernel.acquire_world_lease();
    const auto entity = lease.world().lookup(std::string(logical_name).c_str());
    return entity.is_valid() && entity.is_alive() && entity.has<SimObject>() &&
                   entity.get<Transform>() && entity.get<Velocity>()
               ? entity.id()
               : 0;
}

#undef PILOT_FIELDS
} // namespace runtime::host::integration
