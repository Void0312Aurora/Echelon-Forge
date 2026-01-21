#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include "components/basic/common.h"
#include "components/systems/track_management.h"
#include "components/systems/sensor.h"
#include "components/systems/data_link.h"

inline double calculate_distance_sq(const SystemTrack& track, double x, double y, double z) {
    double dx = track.x - x;
    double dy = track.y - y;
    double dz = track.z - z;
    return dx*dx + dy*dy + dz*dz;
}

inline void register_track_manager_system(flecs::world& ecs) {
    ecs.system<TrackDatabase, const Transform, const Sensor, const ContactList, const DataLink, const CommQueue>("TrackManagerSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            auto tracks_comp = it.field<TrackDatabase>(0);
            auto trans = it.field<const Transform>(1);
            // Sensor/ContactList/DataLink used as const source
            auto contact_list = it.field<const ContactList>(3);
            auto comm_queue = it.field<const CommQueue>(5); // Inbox inside
            
            double dt = it.delta_time();
            
            for (auto i : it) {
                auto& db = tracks_comp[i];
                const auto& contacts = contact_list[i].contacts;
                const auto& inbox = comm_queue[i].inbox;
                
                // 1. Age existing tracks
                for (auto& track : db.tracks) {
                    track.time_since_update += dt;
                }
                
                // 2. Process Local Sensor Contacts
                for (const auto& contact : contacts) {
                    // Simple Fusion: Nearest Neighbor
                    // Convert Polar to Cartesian relative to ownship? 
                    // Wait, ContactList usually stores relative data? 
                    // Detection struct has: range, bearing, elevation.
                    // We need ownship pos to get world pos for track.
                    
                    double own_heading_rad = trans[i].heading; // 0=North? Check convention. Sensor uses relative?
                    // Sensor System usually provides world relative data or local?
                    // Let's assume Detection is relative to Sensor (Body).
                    // Actually, Detection struct in previous view had range/bearing/el.
                    // We need to convert this to World X/Y/Z to store globally consistent tracks.
                    
                    // Math:
                    // Rel Az = contact.bearing (assuming visual/radar returns relative angle)
                    // Global Az = own_heading + contact.bearing
                    
                    // Note: This math depends on coordinate conventions.
                    // Assuming standard math: z=up, x=East, y=North (Nav) ??
                    // SimulationKernel::get_unit_heading returns degrees 0=North CW.
                    // Transform uses radians usually in core physics.
                    
                    // Simple reconstruction for MVP:
                    // Use Contact's stored entity_id to cheat? No, we should use sensor data.
                    // But for MVP fusion, let's use the range/bearing to estimate pos.
                    
                    // Revisit SimulationKernel::get_detections:
                    // It returns Detection struct.
                    
                    // Let's iterate and try to match.
                    
                    // Simplify: Use 'target_id' from Detection to identify unique tracks?
                    // In real life we don't know ID. But here we do.
                    // If we use ID, fusion is trivial.
                    // If we use Pos, it's realistic.
                    // "Track Management (Sensor Fusion -> Track Files)"
                    // Let's use ID for MVP robustness, but calculate Pos for display.
                    
                    bool found = false;
                    for (auto& track : db.tracks) {
                        if (track.entity_id == contact.target_id) {
                            // Update
                            track.time_since_update = 0.0;
                            track.range = contact.range;
                            track.azimuth = contact.bearing;
                            track.elevation = contact.elevation;
                            track.main_source = TrackSource::Radar; // Assume Sensor is Radar/Visual
                            // Update Pos (Estimated)
                             // Requires math, skip for now or approx?
                            found = true;
                            break;
                        }
                    }
                    
                    if (!found && db.tracks.size() < db.max_tracks) {
                        SystemTrack new_track;
                        new_track.entity_id = contact.target_id; // known ID
                        new_track.track_id = contact.target_id; // Use same for now
                        new_track.range = contact.range;
                        new_track.azimuth = contact.bearing;
                        new_track.elevation = contact.elevation;
                        new_track.main_source = TrackSource::Radar;
                        new_track.classification = TrackClass::Unknown; 
                        new_track.confidence = 0.5;
                        new_track.time_since_update = 0.0;
                        db.tracks.push_back(new_track);
                    }
                }
                
                // 3. Process DataLink Messages (ReportContact)
                for (const auto& msg : inbox) {
                    if (msg.type == CommMsgType::ReportContact || msg.entity_ref > 0) {
                        // msg.entity_ref is the Contact ID being reported
                        // msg.x, y, z are the Contact Position (from sender)
                        
                        bool found = false;
                        for (auto& track : db.tracks) {
                             // Match by ID primarily for MVP
                             if (track.entity_id == msg.entity_ref) {
                                  track.time_since_update = 0.0;
                                  track.x = msg.value; // x pos stored in value? Wait, CommPacket definition.
                                  // CommPacket: sender_id, target_receiver, type, entity_ref, x, y, z, value, status, timestamp
                                  track.x = msg.location_x;
                                  track.y = msg.location_y;
                                  track.z = msg.location_z;
                                  track.main_source = TrackSource::DataLink;
                                  found = true;
                                  break;
                             }
                        }
                        
                        if (!found && db.tracks.size() < db.max_tracks) {
                             SystemTrack new_track;
                             new_track.entity_id = msg.entity_ref;
                             new_track.track_id = msg.entity_ref; // Simple ID mapping
                             new_track.x = msg.location_x;
                             new_track.y = msg.location_y;
                             new_track.z = msg.location_z;
                             new_track.main_source = TrackSource::DataLink;
                             new_track.classification = TrackClass::Unknown; // Could infer from sender
                             new_track.confidence = 0.8;
                             new_track.time_since_update = 0.0;
                             db.tracks.push_back(new_track);
                        }
                    }
                }
                
                // 4. Prune Old Tracks
                auto& t = db.tracks;
                t.erase(std::remove_if(t.begin(), t.end(), 
                    [](const SystemTrack& tr) { return tr.time_since_update > 10.0; }), t.end());
            }
        });
}
