#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <vector>
#include "components/basic/common.h"
#include "components/systems/track_management.h"
#include "components/systems/sensor.h"
#include "components/systems/data_link.h"

// Helper to convert spherical relative (Sensor) to Cartesian world
// Note: This is an approximation assuming flat earth for short ranges
inline void spherical_to_cartesian(
    double own_x, double own_y, double own_z,
    double own_heading_deg, 
    double range, double az_rel_deg, double el_deg,
    double& out_x, double& out_y, double& out_z) {
    
    // Convert to Rad
    double combined_az_deg = own_heading_deg + az_rel_deg;
    double az_rad = combined_az_deg * 3.1415926535 / 180.0;
    double el_rad = el_deg * 3.1415926535 / 180.0;
    
    // NAV frame: 0=North (Y+), 90=East (X+)
    // x = r * sin(az) * cos(el) ?? Check conventions.
    // Standard Math: 0=East (X+).
    // Let's stick to simple:
    // Y (North) = R * cos(Az)
    // X (East) = R * sin(Az)
    // Z (Up) = R * sin(El)
    
    double r_cos_el = range * std::cos(el_rad);
    double dy = r_cos_el * std::cos(az_rad);
    double dx = r_cos_el * std::sin(az_rad);
    double dz = range * std::sin(el_rad);
    
    out_x = own_x + dx; // East
    out_y = own_y + dy; // North
    out_z = own_z + dz; // Up
}

// Helper to convert Cartesian world to spherical relative
inline void cartesian_to_spherical(
    double own_x, double own_y, double own_z,
    double own_heading_deg,
    double target_x, double target_y, double target_z,
    double& out_range, double& out_az_rel_deg, double& out_el_deg) {
    
    double dx = target_x - own_x;
    double dy = target_y - own_y;
    double dz = target_z - own_z;
    
    out_range = std::sqrt(dx*dx + dy*dy + dz*dz);
    if (out_range < 1e-3) {
        out_az_rel_deg = 0.0;
        out_el_deg = 0.0;
        return;
    }
    
    // Elevation
    double el_arg = dz / out_range;
    el_arg = std::clamp(el_arg, -1.0, 1.0);
    out_el_deg = std::asin(el_arg) * 180.0 / 3.1415926535;
    
    // Azimuth (Global, 0=North, CW)
    // math_az (0=East, CCW) = atan2(dy, dx)
    // nav_az = 90 - math_az
    // But let's use atan2(x, y) for North-referenced?
    // atan2(x, y) -> returns angle from Y axis (North), CW positive?
    // atan2(dy, dx) is standard.
    
    // Let's use standard map:
    // Az = atan2(dx, dy) -> (East, North). 
    // If dx=1, dy=0 (East) -> Az=PI/2 (90). Valid.
    // If dx=0, dy=1 (North) -> Az=0. Valid.
    double az_global_rad = std::atan2(dx, dy); 
    double az_global_deg = az_global_rad * 180.0 / 3.1415926535;
    
    double az_rel = az_global_deg - own_heading_deg;
    
    // Wrap to [-180, 180]
    while (az_rel > 180.0) az_rel -= 360.0;
    while (az_rel < -180.0) az_rel += 360.0;
    
    out_az_rel_deg = az_rel;
}


inline void register_track_manager_system(flecs::world& ecs) {
    // Only require TrackDatabase + Transform + Sensor Base
    // DataLink is optional
    ecs.system<TrackDatabase, const Transform, const ContactList>("TrackManagerSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            auto tracks_comp = it.field<TrackDatabase>(0);
            auto trans = it.field<const Transform>(1);
            auto contact_list = it.field<const ContactList>(2);
            
            double dt = it.delta_time();
            
            for (auto i : it) {
                auto& db = tracks_comp[i];
                const auto& contacts = contact_list[i].contacts;
                
                // Optional DataLink Access
                const CommQueue* comm_queue = it.entity(i).get<CommQueue>();
                
                // 1. Age existing tracks
                for (auto& track : db.tracks) {
                    track.time_since_update += dt;
                }
                
                double own_heading = trans[i].heading;
                
                // 2. Process Local Sensor Contacts
                for (const auto& contact : contacts) {
                    bool found = false;
                    for (auto& track : db.tracks) {
                        if (track.entity_id == contact.target_id) {
                            track.time_since_update = 0.0;
                            track.range = contact.range;
                            track.azimuth = contact.bearing;
                            track.elevation = contact.elevation;
                            track.main_source = TrackSource::Radar; 
                            
                            // Derive World Pos
                             spherical_to_cartesian(
                                trans[i].x, trans[i].y, trans[i].z, own_heading,
                                track.range, track.azimuth, track.elevation,
                                track.x, track.y, track.z
                            );
                            
                            found = true;
                            break;
                        }
                    }
                    
                    if (!found && db.tracks.size() < (size_t)db.max_tracks) {
                        SystemTrack new_track{}; // Zero-init
                        new_track.entity_id = contact.target_id;
                        new_track.track_id = contact.target_id;
                        new_track.range = contact.range;
                        new_track.azimuth = contact.bearing;
                        new_track.elevation = contact.elevation;
                        new_track.main_source = TrackSource::Radar;
                        new_track.classification = TrackClass::Unknown; 
                        new_track.confidence = 0.5;
                        new_track.time_since_update = 0.0;
                        
                        spherical_to_cartesian(
                            trans[i].x, trans[i].y, trans[i].z, own_heading,
                            new_track.range, new_track.azimuth, new_track.elevation,
                            new_track.x, new_track.y, new_track.z
                        );
                        
                        db.tracks.push_back(new_track);
                    }
                }
                
                // 3. Process DataLink Messages (Strict Filtering)
                if (comm_queue) {
                    for (const auto& msg : comm_queue->inbox) {
                        if (msg.type == CommMsgType::ReportContact) {
                            // msg.entity_ref is the Contact ID being reported
                            // msg.location_x/y/z are the Contact Position
                            
                            bool found = false;
                            for (auto& track : db.tracks) {
                                 if (track.entity_id == msg.entity_ref) {
                                      track.time_since_update = 0.0;
                                      track.x = msg.location_x;
                                      track.y = msg.location_y;
                                      track.z = msg.location_z;
                                      track.main_source = TrackSource::DataLink;
                                      
                                      // Derive Spherical relative to ownship
                                      cartesian_to_spherical(
                                        trans[i].x, trans[i].y, trans[i].z, own_heading,
                                        track.x, track.y, track.z,
                                        track.range, track.azimuth, track.elevation
                                      );
                                      
                                      found = true;
                                      break;
                                 }
                            }
                            
                            if (!found && db.tracks.size() < (size_t)db.max_tracks) {
                                 SystemTrack new_track{}; // Zero-init
                                 new_track.entity_id = msg.entity_ref;
                                 new_track.track_id = msg.entity_ref; 
                                 new_track.x = msg.location_x;
                                 new_track.y = msg.location_y;
                                 new_track.z = msg.location_z;
                                 new_track.main_source = TrackSource::DataLink;
                                 new_track.classification = TrackClass::Unknown;
                                 new_track.confidence = 0.8;
                                 new_track.time_since_update = 0.0;
                                 
                                 cartesian_to_spherical(
                                    trans[i].x, trans[i].y, trans[i].z, own_heading,
                                    new_track.x, new_track.y, new_track.z,
                                    new_track.range, new_track.azimuth, new_track.elevation
                                 );
                                 
                                 db.tracks.push_back(new_track);
                            }
                        }
                    }
                }
                
                // 4. Prune Old Tracks (Compatible with C++17)
                auto& t = db.tracks;
                t.erase(std::remove_if(t.begin(), t.end(), 
                    [](const SystemTrack& tr) { return tr.time_since_update > 10.0; }), t.end());
            }
        });
}
