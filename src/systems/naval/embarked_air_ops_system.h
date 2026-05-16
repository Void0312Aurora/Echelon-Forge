#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/command/legacy_command.h"
#include "components/naval/embarked_air_ops.h"
#include "components/systems/data_link.h"
#include "components/systems/track_management.h"

namespace {

inline double embarked_distance_m(const Transform& a, const Transform& b) {
    const double dx = a.x - b.x;
    const double dy = a.y - b.y;
    const double dz = a.z - b.z;
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

inline bool embarked_has_hostile_track(const TrackDatabase& tracks, std::uint64_t target_id) {
    return std::any_of(
        tracks.tracks.begin(),
        tracks.tracks.end(),
        [&](const SystemTrack& track) {
            return track.entity_id == target_id && track.status == TrackStatus::Confirmed;
        }
    );
}

} // namespace

inline void register_embarked_air_ops_system(flecs::world& ecs) {
    ecs.system<EmbarkedAirOps, const Transform>("EmbarkedAirOpsSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
            const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;

            while (it.next()) {
                auto ops = it.field<EmbarkedAirOps>(0);
                auto host_transform = it.field<const Transform>(1);
                for (auto i : it) {
                    flecs::entity host = it.entity(i);
                    auto& state = ops[i];
                    if (!state.enabled || state.active_helo_entity_id == 0) {
                        continue;
                    }

                    flecs::entity helo = it.world().entity(state.active_helo_entity_id);
                    if (!helo.is_valid()) {
                        state.active_helo_entity_id = 0;
                        state.helo_airborne = false;
                        continue;
                    }

                    Transform* helo_transform = helo.get_mut<Transform>();
                    Velocity* helo_velocity = helo.get_mut<Velocity>();
                    MissionCommand* helo_mission = helo.get_mut<MissionCommand>();
                    MovementCommand* helo_move = helo.get_mut<MovementCommand>();
                    const MissionCommand* host_mission = host.get<MissionCommand>();
                    if (!helo_transform || !helo_velocity || !helo_mission) {
                        continue;
                    }

                    if (state.helo_airborne) {
                        if (helo_transform->z < state.launch_altitude_m * 0.5) {
                            helo_transform->z = state.launch_altitude_m;
                        }
                    } else {
                        helo_transform->x = host_transform[i].x;
                        helo_transform->y = host_transform[i].y;
                        helo_transform->z = host_transform[i].z;
                        helo_transform->heading = host_transform[i].heading;
                        helo_velocity->vx = 0.0;
                        helo_velocity->vy = 0.0;
                        helo_velocity->vz = 0.0;
                    }

                    if (!host_mission || !host_mission->active) {
                        continue;
                    }

                    if (host_mission->embarked_helo_entity_id != 0 &&
                        host_mission->embarked_helo_entity_id != state.active_helo_entity_id) {
                        continue;
                    }
                    helo_mission->active = state.helo_airborne;

                    // command_code 31/32/33 are reserved for naval embarked-air token MVP.
                    if (host_mission->launch_helo || host_mission->command_code == 31) {
                        state.helo_airborne = true;
                        const double heading_rad = Math::to_radians(host_transform[i].heading);
                        const double right_rad = Math::to_radians(host_transform[i].heading + 90.0);
                        helo_transform->x = host_transform[i].x +
                            std::sin(heading_rad) * state.launch_offset_forward_m +
                            std::sin(right_rad) * state.launch_offset_starboard_m;
                        helo_transform->y = host_transform[i].y +
                            std::cos(heading_rad) * state.launch_offset_forward_m +
                            std::cos(right_rad) * state.launch_offset_starboard_m;
                        helo_transform->z = std::max(state.launch_altitude_m, host_transform[i].z + state.launch_altitude_m);
                        const double speed_mps = host_mission->cmd_speed_mps > 0.0 ? host_mission->cmd_speed_mps : 55.0;
                        helo_velocity->vx = std::sin(heading_rad) * speed_mps;
                        helo_velocity->vy = std::cos(heading_rad) * speed_mps;
                        helo_velocity->vz = 0.0;
                        if (helo_move) {
                            helo_move->active = true;
                            helo_move->target_heading = host_transform[i].heading;
                            helo_move->target_speed = speed_mps;
                            helo_move->target_altitude = helo_transform->z;
                        }
                    } else if (host_mission->recover_helo || host_mission->command_code == 32) {
                        // Token-level recovery MVP: once commanded, snap the helo back onto the flight deck.
                        state.helo_airborne = false;
                        helo_transform->x = host_transform[i].x;
                        helo_transform->y = host_transform[i].y;
                        helo_transform->z = host_transform[i].z;
                        helo_transform->heading = host_transform[i].heading;
                        helo_velocity->vx = 0.0;
                        helo_velocity->vy = 0.0;
                        helo_velocity->vz = 0.0;
                        helo_mission->active = false;
                        if (helo_move) {
                            helo_move->active = false;
                        }
                    } else if ((host_mission->relay_oth_targeting || host_mission->command_code == 33) && state.relay_oth_targeting) {
                        if ((current_time - helo_mission->takeoff_interval_s) < state.relay_refresh_s) {
                            continue;
                        }
                        TrackDatabase* helo_tracks = helo.get_mut<TrackDatabase>();
                        TrackDatabase* host_tracks = host.get_mut<TrackDatabase>();
                        if (!helo_tracks || !host_tracks || host_mission->assigned_target_id == 0) {
                            continue;
                        }
                        if (!embarked_has_hostile_track(*helo_tracks, host_mission->assigned_target_id)) {
                            continue;
                        }

                        for (const auto& track : helo_tracks->tracks) {
                            if (track.entity_id != host_mission->assigned_target_id) {
                                continue;
                            }
                            auto existing = std::find_if(
                                host_tracks->tracks.begin(),
                                host_tracks->tracks.end(),
                                [&](const SystemTrack& current) {
                                    return current.entity_id == track.entity_id || current.track_id == track.track_id;
                                }
                            );
                            SystemTrack relayed = track;
                            relayed.main_source = TrackSource::DataLink;
                            relayed.last_datalink_update_time = current_time;
                            relayed.status = TrackStatus::Confirmed;
                            relayed.quality = std::max(relayed.quality, 0.7);
                            relayed.confidence = std::max(relayed.confidence, 0.7);
                            if (existing == host_tracks->tracks.end()) {
                                host_tracks->tracks.push_back(relayed);
                            } else {
                                *existing = relayed;
                            }
                            helo_mission->takeoff_interval_s = current_time;
                            break;
                        }
                    }
                }
            }
        });
}
