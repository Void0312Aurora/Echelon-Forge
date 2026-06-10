#pragma once

#include <flecs.h>
#include <vector>
#include <unordered_map>
#include "components/systems/data_link.h"
#include "components/systems/sensor.h"
#include "components/systems/track_management.h"
#include "components/systems/comm.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/command/legacy_command_bridge.h"
#include <spdlog/spdlog.h>
#include <cmath>
#include <limits>

namespace {
inline double data_link_effective_height_m(flecs::entity entity, const Transform& transform) {
    double height_m = std::max(0.0, transform.z);
    if (const ShipPlatform* ship = entity.get<ShipPlatform>()) {
        height_m += std::max(0.0, ship->height_above_waterline_m);
    }
    return height_m;
}

inline bool data_link_pair_is_eligible(
    const flecs::entity& sender_entity,
    const DataLink& sender_link,
    const Transform& sender_trans,
    double sender_effective_height_m,
    const flecs::entity& receiver_entity,
    const DataLink& receiver_link,
    const Transform& receiver_trans,
    double receiver_effective_height_m
) {
    if (sender_entity == receiver_entity) {
        return false;
    }
    if (!receiver_link.active) {
        return false;
    }
    if (sender_link.network_id != receiver_link.network_id) {
        return false;
    }

    const double dx = sender_trans.x - receiver_trans.x;
    const double dy = sender_trans.y - receiver_trans.y;
    const double dz = sender_trans.z - receiver_trans.z;
    const double dist_km = std::sqrt(dx * dx + dy * dy + dz * dz) / 1000.0;
    if (dist_km > sender_link.max_range_km) {
        return false;
    }

    const double horizon_km =
        3.57 * (std::sqrt(sender_effective_height_m) + std::sqrt(receiver_effective_height_m));
    if (dist_km > horizon_km) {
        return false;
    }

    const Alliance* s_side = sender_entity.get<Alliance>();
    const Alliance* r_side = receiver_entity.get<Alliance>();
    return s_side && r_side && s_side->side == r_side->side;
}

inline double data_link_sender_local_support_window_s(const Sensor* sensor) {
    if (!sensor) {
        return 1.0;
    }
    return std::min(
        track_recent_local_support_window_s(sensor->scan_period),
        std::max(1.0, sensor->track_memory_s)
    );
}

} // namespace

 inline void register_data_link_system(flecs::world& ecs) {
    // We run after SensorSystem to fuse the new contacts
    ecs.system<const DataLink, const Transform, const ContactList, const TrackDatabase, const Sensor>("DataLinkFusionSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            // Need random access to all data links to form pairs
            // We'll collect pointers to them first
            struct LinkNode {
                flecs::entity entity;
                const DataLink* link;
                const Transform* trans;
                const ContactList* contacts;
                const TrackDatabase* track_db;
                const Sensor* sensor;
                double effective_height_m;
            };
            std::vector<LinkNode> nodes;
            
            // Iterate and collect
            while (it.next()) {
                 auto link = it.field<const DataLink>(0);
                 auto trans = it.field<const Transform>(1);
                 auto contacts = it.field<const ContactList>(2);
                 auto track_db = it.field<const TrackDatabase>(3);
                 auto sensor = it.field<const Sensor>(4);
                 
                 for (auto i : it) {
                     nodes.push_back({
                         it.entity(i),
                         &link[i],
                         &trans[i],
                         &contacts[i],
                         &track_db[i],
                         &sensor[i],
                         data_link_effective_height_m(it.entity(i), trans[i])
                     });
                 }
            }
            
             // P2P Sharing Loop (O(N^2))
            const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
            double current_time = info ? (double)info->world_time_total : 0.0;

            for (const auto& sender : nodes) {
                if (!sender.link->active) continue;
                DataLink* sender_link_mut = sender.entity.get_mut<DataLink>();
                if (!sender_link_mut) {
                    continue;
                }
                sender_link_mut->reports_sent_last_update = 0;
                sender_link_mut->messages_sent_last_update = 0;
                sender_link_mut->reports_dropped_last_update = 0;
                sender_link_mut->messages_dropped_last_update = 0;

                // 1. Data Fusion (Always)
                bool has_tracks = sender.track_db && !sender.track_db->tracks.empty();
                
                // 2. Messaging remains a compatibility-only legacy command seam.
                ActionCommand* cmd = sender.entity.get_mut<ActionCommand>();
                const auto message_command = resolve_compatibility_message_command(sender.entity);
                const bool sending_msg = message_command.send;
                int report_budget_remaining = std::max(0, sender.link->max_reports_per_update);
                int message_budget_remaining = std::max(0, sender.link->max_messages_per_update);

                if (!has_tracks && !sending_msg) continue;

                if (sending_msg) {
                    for (auto& receiver : nodes) {
                        if (!data_link_pair_is_eligible(
                                sender.entity,
                                *sender.link,
                                *sender.trans,
                                sender.effective_height_m,
                                receiver.entity,
                                *receiver.link,
                                *receiver.trans,
                                receiver.effective_height_m
                            )) {
                            continue;
                        }

                        if (message_command.recipient != 0 && message_command.recipient != receiver.entity.id()) {
                            continue;
                        }

                        if (message_budget_remaining <= 0) {
                            sender_link_mut->messages_dropped_last_update += 1;
                            sender_link_mut->messages_dropped_total += 1;
                            continue;
                        }

                        CommQueue* q = receiver.entity.get_mut<CommQueue>();
                        if (!q) {
                            continue;
                        }

                        q->inbox.push_back({
                            sender.entity.id(),
                            message_command.recipient, // 0 if broadcast
                            static_cast<CommMsgType>(message_command.msg_type),
                            message_command.arg,
                            0, // track_ref
                            sender.trans->x,
                            sender.trans->y,
                            sender.trans->z,
                            0.0, // velocity_x
                            0.0, // velocity_y
                            0.0, // velocity_z
                            0.0, // value (default 0 as ActionCommand doesn't have it)
                            0.0, // quality
                            0,   // status_code
                            current_time // Actual Timestamp
                        });
                        --message_budget_remaining;
                        sender_link_mut->messages_sent_last_update += 1;
                        sender_link_mut->messages_sent_total += 1;
                        spdlog::trace("Msg delivered from {} to {}", sender.entity.id(), receiver.entity.id());
                    }
                }

                for (auto& receiver : nodes) {
                    if (!data_link_pair_is_eligible(
                            sender.entity,
                            *sender.link,
                            *sender.trans,
                            sender.effective_height_m,
                            receiver.entity,
                            *receiver.link,
                            *receiver.trans,
                            receiver.effective_height_m
                        )) {
                        continue;
                    }

                    // --- TASK 1: TRACK REPORTING ---
                    if (has_tracks) {
                        CommQueue* q = receiver.entity.get_mut<CommQueue>();
                        if (q) {
                            const TrackDatabase* receiver_db = receiver.track_db;
                            const double sender_local_support_window_s =
                                data_link_sender_local_support_window_s(sender.sensor);
                            for (const auto& trk : sender.track_db->tracks) {
                                if (trk.status != TrackStatus::Confirmed) {
                                    continue;
                                }
                                if (trk.last_datalink_update_time >= 0.0) {
                                    continue;
                                }
                                if (!track_has_recent_local_support(trk, current_time, sender_local_support_window_s)) {
                                    continue;
                                }
                                bool should_report = true;
                                if (receiver_db != nullptr) {
                                    for (const auto& known : receiver_db->tracks) {
                                        const bool same_track =
                                            (known.entity_id != 0 && known.entity_id == trk.entity_id)
                                            || (known.track_id != 0 && known.track_id == trk.track_id);
                                        if (!same_track) {
                                            continue;
                                        }
                                        const double pos_dx = known.x - trk.x;
                                        const double pos_dy = known.y - trk.y;
                                        const double pos_dz = known.z - trk.z;
                                        const double vel_dx = known.vx - trk.vx;
                                        const double vel_dy = known.vy - trk.vy;
                                        const double vel_dz = known.vz - trk.vz;
                                        const double pos_delta_m = std::sqrt(pos_dx * pos_dx + pos_dy * pos_dy + pos_dz * pos_dz);
                                        const double vel_delta_mps = std::sqrt(vel_dx * vel_dx + vel_dy * vel_dy + vel_dz * vel_dz);
                                        const double since_last_dl = known.last_datalink_update_time < 0.0
                                            ? std::numeric_limits<double>::infinity()
                                            : (current_time - known.last_datalink_update_time);
                                        should_report = pos_delta_m > 500.0 || vel_delta_mps > 2.0 || since_last_dl >= 5.0;
                                        break;
                                    }
                                }
                                if (!should_report) {
                                    continue;
                                }
                                if (report_budget_remaining <= 0) {
                                    sender_link_mut->reports_dropped_last_update += 1;
                                    sender_link_mut->reports_dropped_total += 1;
                                    continue;
                                }
                                q->inbox.push_back({
                                    sender.entity.id(),
                                    receiver.entity.id(),
                                    CommMsgType::ReportTrack,
                                    trk.entity_id,
                                    trk.track_id,
                                    trk.x,
                                    trk.y,
                                    trk.z,
                                    trk.vx,
                                    trk.vy,
                                    trk.vz,
                                    0.0,
                                    trk.quality,
                                    static_cast<int>(trk.classification),
                                    current_time
                                });
                                --report_budget_remaining;
                                sender_link_mut->reports_sent_last_update += 1;
                                sender_link_mut->reports_sent_total += 1;
                            }
                        }
                    }

                }
                
                // Clear the Message Trigger
                if (sending_msg && cmd) {
                    cmd->send_msg = false;
                }
            }
        });

    // Clear Inbox System (TTL-based Pruning)
    ecs.system<CommQueue>("ClearCommInbox")
       .kind(flecs::PreUpdate)
       .run([](flecs::iter& it) {
           const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
           double time = info ? (double)info->world_time_total : 0.0;
           constexpr double kMessageTTL = 0.5; // Keep messages for 0.5s

           while(it.next()) {
                auto q = it.field<CommQueue>(0);
                for(auto i : it) {
                    // Remove messages older than TTL
                    std::erase_if(q[i].inbox, [time](const CommPacket& pkg) {
                        return (time - pkg.timestamp) > kMessageTTL;
                    });
                }
           }
       });
}
