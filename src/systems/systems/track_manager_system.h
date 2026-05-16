#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include <vector>
#include <limits>
#include "components/basic/common.h"
#include "components/systems/track_management.h"
#include "components/systems/sensor.h"
#include "components/systems/data_link.h"
#include "components/systems/comm.h"

inline TrackClass classify_track_from_alliance(
    const Alliance* owner_alliance,
    const Alliance* target_alliance
) {
    if (!owner_alliance || !target_alliance) {
        return TrackClass::Unknown;
    }
    if (target_alliance->side == Side::Neutral || target_alliance->side == Side::Unknown) {
        return TrackClass::Neutral;
    }
    return owner_alliance->side == target_alliance->side ? TrackClass::Friendly : TrackClass::Hostile;
}

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

inline double track_quality_from_counts(int hits, int window_n, double time_since_update) {
    const int clamped_window = std::max(window_n, 1);
    const double hit_term = std::clamp(static_cast<double>(hits) / static_cast<double>(clamped_window), 0.0, 1.0);
    const double age_term = std::clamp(1.0 - (time_since_update / 10.0), 0.0, 1.0);
    return std::clamp(0.7 * hit_term + 0.3 * age_term, 0.0, 1.0);
}

inline TrackSource local_track_source_from_contact(const Detection& contact) {
    if (contact.sensor_type == static_cast<int>(SensorType::ESM) || contact.range <= 0.0) {
        return TrackSource::RWR;
    }
    if (contact.sensor_type == static_cast<int>(SensorType::Sonar)) {
        return TrackSource::Sonar;
    }
    return TrackSource::Radar;
}

inline void predict_track(SystemTrack& track, double dt) {
    track.x += track.vx * dt;
    track.y += track.vy * dt;
    track.z += track.vz * dt;
}

inline void alpha_beta_update(
    SystemTrack& track,
    double meas_x,
    double meas_y,
    double meas_z,
    double dt
) {
    const double alpha = std::clamp(track.alpha_beta_alpha, 0.0, 1.0);
    const double beta = std::max(0.0, track.alpha_beta_beta);

    const double rx = meas_x - track.x;
    const double ry = meas_y - track.y;
    const double rz = meas_z - track.z;

    track.x += alpha * rx;
    track.y += alpha * ry;
    track.z += alpha * rz;

    if (dt > 1.0e-6) {
        const double beta_over_dt = beta / dt;
        track.vx += beta_over_dt * rx;
        track.vy += beta_over_dt * ry;
        track.vz += beta_over_dt * rz;
    }
}

inline SystemTrack make_track_from_contact(
    const Detection& contact,
    const Transform& own_transform,
    const Alliance* owner_alliance,
    flecs::world world,
    double current_time,
    const Sensor* sensor_cfg
) {
    SystemTrack track{};
    track.entity_id = contact.target_id;
    track.track_id = contact.target_id;
    track.range = contact.range;
    track.azimuth = contact.bearing;
    track.elevation = contact.elevation;
    track.main_source = local_track_source_from_contact(contact);
    track.local_source = track.main_source;
    const Alliance* target_alliance = world.entity(contact.target_id).get<Alliance>();
    track.classification = classify_track_from_alliance(owner_alliance, target_alliance);
    track.status = TrackStatus::Tentative;
    track.confidence = 0.25;
    track.quality = 0.25;
    track.time_since_update = 0.0;
    track.last_local_update_time = current_time;
    if (sensor_cfg) {
        track.alpha_beta_alpha = sensor_cfg->alpha_beta_alpha > 0.0 ? sensor_cfg->alpha_beta_alpha : 0.65;
        track.alpha_beta_beta = sensor_cfg->alpha_beta_beta > 0.0 ? sensor_cfg->alpha_beta_beta : 0.12;
        track.confirm_hit_count = 1;
        track.confirm_window_progress = 1;
    } else {
        track.confirm_hit_count = 1;
        track.confirm_window_progress = 1;
    }

    spherical_to_cartesian(
        own_transform.x, own_transform.y, own_transform.z, own_transform.heading,
        track.range, track.azimuth, track.elevation,
        track.x, track.y, track.z
    );
    refresh_track_source(track, current_time, sensor_cfg ? track_recent_local_support_window_s(sensor_cfg->scan_period) : 1.0);
    refresh_track_identification(track);
    return track;
}

inline SystemTrack make_track_from_report(
    const CommPacket& msg,
    const Transform& own_transform,
    const Alliance* owner_alliance,
    flecs::world world,
    double current_time
) {
    SystemTrack track{};
    track.entity_id = msg.entity_ref;
    track.track_id = msg.track_ref != 0 ? msg.track_ref : msg.entity_ref;
    track.x = msg.location_x;
    track.y = msg.location_y;
    track.z = msg.location_z;
    track.vx = msg.velocity_x;
    track.vy = msg.velocity_y;
    track.vz = msg.velocity_z;
    track.main_source = TrackSource::DataLink;
    track.local_source = TrackSource::None;
    const Alliance* target_alliance = world.entity(msg.entity_ref).get<Alliance>();
    track.classification = classify_track_from_alliance(owner_alliance, target_alliance);
    track.status = TrackStatus::Confirmed;
    track.confidence = std::max(0.5, msg.quality);
    track.quality = std::max(0.5, msg.quality);
    track.time_since_update = 0.0;
    track.last_datalink_update_time = current_time;
    track.confirm_hit_count = 2;
    track.confirm_window_progress = 2;

    cartesian_to_spherical(
        own_transform.x, own_transform.y, own_transform.z, own_transform.heading,
        track.x, track.y, track.z,
        track.range, track.azimuth, track.elevation
    );
    refresh_track_source(track, current_time, 1.0);
    refresh_track_identification(track);
    return track;
}

inline void rebuild_public_tracks(TrackDatabase& db) {
    std::erase_if(db.tracks, [](const SystemTrack& track) {
        return track.status == TrackStatus::Tentative;
    });
}

inline void register_track_manager_system(flecs::world& ecs) {
    // Only require TrackDatabase + Transform + Sensor Base
    // DataLink is optional
    ecs.system<TrackDatabase, const Transform, const ContactList, const Sensor>("TrackManagerSystem")
        .kind(flecs::OnUpdate)
        .run([](flecs::iter& it) {
            while (it.next()) {
                auto tracks_comp = it.field<TrackDatabase>(0);
                auto trans = it.field<const Transform>(1);
                auto contact_list = it.field<const ContactList>(2);
                auto sensor = it.field<const Sensor>(3);
                const double dt = it.delta_time();
                const ecs_world_info_t* info = ecs_get_world_info(it.world().c_ptr());
                const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;

                for (auto i : it) {
                    auto& db = tracks_comp[i];
                    const auto& contacts = contact_list[i].contacts;
                    const Alliance* owner_alliance = it.entity(i).get<Alliance>();

                    // Optional DataLink Access
                    const CommQueue* comm_queue = it.entity(i).get<CommQueue>();
                    const double local_support_window_s = track_recent_local_support_window_s(sensor[i].scan_period);

                    // 1. Age existing public tracks
                    for (auto& track : db.tracks) {
                        track.time_since_update += dt;
                        predict_track(track, dt);
                        if (track.status == TrackStatus::Confirmed && track.time_since_update > sensor[i].track_memory_s) {
                            track.status = TrackStatus::Coasted;
                        }
                        track.quality = track_quality_from_counts(track.confirm_hit_count, std::max(sensor[i].confirm_window_n, 1), track.time_since_update);
                        track.confidence = track.quality;
                        refresh_track_source(track, current_time, local_support_window_s);
                        refresh_track_identification(track);
                    }
                    for (auto& track : db.tentative_tracks) {
                        track.time_since_update += dt;
                        predict_track(track, dt);
                        track.quality = track_quality_from_counts(track.confirm_hit_count, std::max(sensor[i].confirm_window_n, 1), track.time_since_update);
                        track.confidence = track.quality;
                        refresh_track_source(track, current_time, local_support_window_s);
                        refresh_track_identification(track);
                    }

                    double own_heading = trans[i].heading;

                    // 2. Process Local Sensor Contacts
                    for (const auto& contact : contacts) {
                        double meas_x = 0.0;
                        double meas_y = 0.0;
                        double meas_z = 0.0;
                        spherical_to_cartesian(
                            trans[i].x, trans[i].y, trans[i].z, own_heading,
                            contact.range, contact.bearing, contact.elevation,
                            meas_x, meas_y, meas_z
                        );

                        bool found = false;
                        for (auto& track : db.tracks) {
                            if (track.entity_id == contact.target_id) {
                                track.time_since_update = 0.0;
                                track.range = contact.range;
                                track.azimuth = contact.bearing;
                                track.elevation = contact.elevation;
                                track.local_source = local_track_source_from_contact(contact);
                                const Alliance* target_alliance = it.world().entity(contact.target_id).get<Alliance>();
                                track.classification = classify_track_from_alliance(owner_alliance, target_alliance);
                                track.status = TrackStatus::Confirmed;
                                track.last_local_update_time = current_time;
                                track.confirm_hit_count = std::min(track.confirm_hit_count + 1, std::max(sensor[i].confirm_window_n, 1));
                                track.confirm_window_progress = std::min(track.confirm_window_progress + 1, std::max(sensor[i].confirm_window_n, 1));
                                alpha_beta_update(track, meas_x, meas_y, meas_z, std::max(dt, sensor[i].scan_period));
                                track.quality = track_quality_from_counts(track.confirm_hit_count, std::max(sensor[i].confirm_window_n, 1), track.time_since_update);
                                track.confidence = track.quality;
                                refresh_track_source(track, current_time, local_support_window_s);
                                refresh_track_identification(track);

                                found = true;
                                break;
                            }
                        }
                        if (found) {
                            continue;
                        }

                        for (auto it_tent = db.tentative_tracks.begin(); it_tent != db.tentative_tracks.end(); ++it_tent) {
                            auto& track = *it_tent;
                            if (track.entity_id != contact.target_id) {
                                continue;
                            }

                            track.time_since_update = 0.0;
                            track.range = contact.range;
                            track.azimuth = contact.bearing;
                            track.elevation = contact.elevation;
                            track.local_source = local_track_source_from_contact(contact);
                            const Alliance* target_alliance = it.world().entity(contact.target_id).get<Alliance>();
                            track.classification = classify_track_from_alliance(owner_alliance, target_alliance);
                            track.last_local_update_time = current_time;
                            track.confirm_hit_count += 1;
                            track.confirm_window_progress = std::min(track.confirm_window_progress + 1, std::max(sensor[i].confirm_window_n, 1));
                            alpha_beta_update(track, meas_x, meas_y, meas_z, std::max(dt, sensor[i].scan_period));
                            track.quality = track_quality_from_counts(track.confirm_hit_count, std::max(sensor[i].confirm_window_n, 1), track.time_since_update);
                            track.confidence = track.quality;
                            refresh_track_source(track, current_time, local_support_window_s);
                            refresh_track_identification(track);

                            if (track.confirm_hit_count >= std::max(sensor[i].confirm_hits_m, 1)
                                && track.confirm_window_progress <= std::max(sensor[i].confirm_window_n, 1)) {
                                track.status = TrackStatus::Confirmed;
                                db.tracks.push_back(track);
                                db.tentative_tracks.erase(it_tent);
                            }
                            found = true;
                            break;
                        }

                        if (!found && (db.tracks.size() + db.tentative_tracks.size()) < static_cast<size_t>(db.max_tracks)) {
                            db.tentative_tracks.push_back(
                                make_track_from_contact(contact, trans[i], owner_alliance, it.world(), current_time, &sensor[i])
                            );
                        }
                    }

                    // 3. Process DataLink Messages (Strict Filtering)
                    if (comm_queue) {
                        for (const auto& msg : comm_queue->inbox) {
                            if (msg.type == CommMsgType::ReportTrack || msg.type == CommMsgType::ReportContact) {
                                bool found = false;
                                for (auto& track : db.tracks) {
                                    if (track.entity_id == msg.entity_ref || track.track_id == msg.track_ref) {
                                        track.time_since_update = 0.0;
                                        track.x = msg.location_x;
                                        track.y = msg.location_y;
                                        track.z = msg.location_z;
                                        if (!track_has_local_geometry_this_update(track, current_time)) {
                                            track.vx = msg.velocity_x;
                                            track.vy = msg.velocity_y;
                                            track.vz = msg.velocity_z;
                                        }
                                        const Alliance* target_alliance = it.world().entity(msg.entity_ref).get<Alliance>();
                                        track.classification = classify_track_from_alliance(owner_alliance, target_alliance);
                                        track.status = TrackStatus::Confirmed;
                                        track.last_datalink_update_time = current_time;
                                        track.quality = std::max(track.quality, msg.quality);
                                        track.confidence = std::max(track.confidence, msg.quality);
                                        track.confirm_hit_count = std::max(track.confirm_hit_count, std::max(sensor[i].confirm_hits_m, 1));
                                        track.iff_known = true;

                                        cartesian_to_spherical(
                                            trans[i].x, trans[i].y, trans[i].z, own_heading,
                                            track.x, track.y, track.z,
                                            track.range, track.azimuth, track.elevation
                                        );
                                        refresh_track_source(track, current_time, local_support_window_s);
                                        refresh_track_identification(track);

                                        found = true;
                                        break;
                                    }
                                }

                                if (!found && db.tracks.size() < static_cast<size_t>(db.max_tracks)) {
                                    db.tracks.push_back(
                                        make_track_from_report(msg, trans[i], owner_alliance, it.world(), current_time)
                                    );
                                }
                            }
                        }
                    }

                    std::erase_if(db.tentative_tracks, [&](const SystemTrack& tr) {
                        return tr.time_since_update > std::max(sensor[i].track_memory_s, sensor[i].scan_period * std::max(sensor[i].confirm_window_n, 1));
                    });

                    auto& t = db.tracks;
                    t.erase(
                        std::remove_if(
                            t.begin(),
                            t.end(),
                            [](const SystemTrack& tr) { return tr.time_since_update > 10.0; }
                        ),
                        t.end()
                    );
                    rebuild_public_tracks(db);
                }
            }
        });
}
