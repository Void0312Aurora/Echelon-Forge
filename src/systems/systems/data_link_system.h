#pragma once

#include <flecs.h>
#include <vector>
#include <unordered_map>
#include "components/systems/data_link.h"
#include "components/systems/sensor.h"
#include "components/systems/comm.h"
#include "components/physics/action.h"
#include <spdlog/spdlog.h>

 inline void register_data_link_system(flecs::world& ecs) {
    // We run after SensorSystem to fuse the new contacts
    ecs.system<const DataLink, const Transform, ContactList>("DataLinkFusionSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            // Need random access to all data links to form pairs
            // We'll collect pointers to them first
            struct LinkNode {
                flecs::entity entity;
                const DataLink* link;
                const Transform* trans;
                ContactList* contacts;
            };
            std::vector<LinkNode> nodes;
            
            // Iterate and collect
            while (it.next()) {
                 auto link = it.field<const DataLink>(0);
                 auto trans = it.field<const Transform>(1);
                 auto contacts = it.field<ContactList>(2);
                 
                 for (auto i : it) {
                     nodes.push_back({it.entity(i), &link[i], &trans[i], &contacts[i]});
                 }
            }
            
             // P2P Sharing Loop (O(N^2))
            const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
            double current_time = info ? (double)info->world_time_total : 0.0;

            for (const auto& sender : nodes) {
                if (!sender.link->active) continue;

                // 1. Data Fusion (Always)
                bool has_contacts = !sender.contacts->contacts.empty();
                
                // 2. Messaging (If Triggered)
                // We need to access ActionCommand. But it wasn't in the query.
                // We can get it from entity.
                ActionCommand* cmd = sender.entity.get_mut<ActionCommand>();
                bool sending_msg = (cmd && cmd->send_msg);

                if (!has_contacts && !sending_msg) continue;

                for (auto& receiver : nodes) {
                    if (sender.entity == receiver.entity) {
                        // Skip self, but if this is the end of loop, we might need to clear
                        continue;
                    }
                    if (!receiver.link->active) continue;
                    if (sender.link->network_id != receiver.link->network_id) continue;
                    
                    // Physical Check
                    double dx = sender.trans->x - receiver.trans->x;
                    double dy = sender.trans->y - receiver.trans->y;
                    double dz = sender.trans->z - receiver.trans->z;
                    double dist_eval = std::sqrt(dx*dx + dy*dy + dz*dz); // meters
                    double dist_km = dist_eval / 1000.0;
                    
                    if (dist_km > sender.link->max_range_km) continue;
                    
                    // LOS Check
                    double h1 = std::max(0.0, sender.trans->z);
                    double h2 = std::max(0.0, receiver.trans->z);
                    double horizon_km = 3.57 * (std::sqrt(h1) + std::sqrt(h2));
                    
                    if (dist_km > horizon_km) continue;

                    // Security Check: Alliance Match
                    const Alliance* s_side = sender.entity.get<Alliance>();
                    const Alliance* r_side = receiver.entity.get<Alliance>();
                    if (!s_side || !r_side || s_side->side != r_side->side) continue;

                    // --- TASK 1: FUSION ---
                    if (has_contacts) {
                        std::vector<uint64_t> receiver_known_ids;
                        receiver_known_ids.reserve(receiver.contacts->contacts.size());
                        for(const auto& c : receiver.contacts->contacts) receiver_known_ids.push_back(c.target_id);
                        
                        for (const auto& det : sender.contacts->contacts) {
                            bool known = false;
                            for(auto id : receiver_known_ids) if(id == det.target_id) { known=true; break; }
                            if(known) continue;
                            
                            auto target_e = it.world().entity(det.target_id);
                            if (!target_e.is_valid()) continue;
                            const Transform* t_t = target_e.get<Transform>();
                            if (!t_t) continue;
                            
                            double t_dx = t_t->x - receiver.trans->x;
                            double t_dy = t_t->y - receiver.trans->y;
                            double t_dz = t_t->z - receiver.trans->z;
                            
                            double t_dist = std::sqrt(t_dx*t_dx + t_dy*t_dy + t_dz*t_dz);
                            double bearing_rad = std::atan2(t_dy, t_dx);
                            double bearing_deg = bearing_rad * 180.0 / 3.14159265359;
                            double bearing_nav = 90.0 - bearing_deg;
                            while(bearing_nav < 0) bearing_nav += 360.0;
                            while(bearing_nav >= 360.0) bearing_nav -= 360.0;
                            
                            double rel_bearing = bearing_nav - receiver.trans->heading;
                            while (rel_bearing > 180.0) rel_bearing -= 360.0;
                            while (rel_bearing < -180.0) rel_bearing += 360.0;
                            
                            Detection shared = det;
                            shared.range = t_dist;
                            shared.bearing = rel_bearing;
                            
                            receiver.contacts->contacts.push_back(shared);
                            receiver_known_ids.push_back(det.target_id);
                        }
                    }

                    // --- TASK 2: MESSAGING ---
                    if (sending_msg) {
                        // Check Recipient
                        if (cmd->msg_recipient == 0 || cmd->msg_recipient == receiver.entity.id()) {
                            // Deliver
                            CommQueue* q = receiver.entity.get_mut<CommQueue>();
                            if (q) {
                                q->inbox.push_back({
                                    sender.entity.id(),
                                    cmd->msg_recipient, // 0 if broadcast
                                    static_cast<CommMsgType>(cmd->msg_type),
                                    cmd->msg_arg,
                                    sender.trans->x, sender.trans->y, sender.trans->z,
                                    0.0, // value (default 0 as ActionCommand doesn't have it)
                                    0,   // status_code
                                    current_time // Actual Timestamp
                                });
                                spdlog::trace("Msg delivered from {} to {}", sender.entity.id(), receiver.entity.id());
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
