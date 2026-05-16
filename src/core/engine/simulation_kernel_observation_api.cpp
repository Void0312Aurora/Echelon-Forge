#include "simulation_kernel.h"

#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/combat/weapon.h"
#include "components/physics/dynamics.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/ew.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/systems/track_management.h"

#include <spdlog/spdlog.h>

#include <cmath>
#include <limits>
#include <vector>

std::vector<double> SimulationKernel::get_unit_position(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Transform* t = e.get<Transform>();
        if (t) {
            return {t->x, t->y, t->z};
        }
    }
    return {0.0, 0.0, 0.0};
}

std::vector<Detection> SimulationKernel::get_detections(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList* c = e.get<ContactList>();
        if (c) {
            return c->contacts;
        }
    }
    return {};
}

void SimulationKernel::set_contact_list(uint64_t entity_id, const std::vector<Detection>& detections) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        ContactList contacts{};
        contacts.contacts = detections;
        e.set<ContactList>(contacts);
    } else {
        spdlog::warn("Attempted to set contact list for invalid entity ID: {}", entity_id);
    }
}

double SimulationKernel::debug_get_last_scan_time(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Sensor* s = e.get<Sensor>();
        if (s) return s->last_scan_time;
    }
    return std::numeric_limits<double>::quiet_NaN();
}

int SimulationKernel::debug_get_contact_count(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList* c = e.get<ContactList>();
        if (c) return static_cast<int>(c->contacts.size());
    }
    return -1;
}

std::vector<double> SimulationKernel::debug_get_mass_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {};

    const Mass* mass = e.get<Mass>();
    const MassProperties* props = e.get<MassProperties>();
    if (!mass || !props) return {};

    return {
        mass->empty_mass_kg,
        mass->fuel_mass_kg,
        mass->stores_mass_kg,
        mass->get_total_kg(),
        props->empty_mass_kg,
        props->current_total_mass_kg,
    };
}

std::vector<double> SimulationKernel::get_unit_health(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {0.0, 0.0};

    if (const Health* h = e.get<Health>()) {
        return {h->current_hp, h->max_hp};
    }
    return {0.0, 0.0};
}

std::vector<double> SimulationKernel::get_unit_fuel(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const FuelSystem* f = e.get<FuelSystem>()) {
            return {f->internal_fuel_kg, f->max_internal_fuel_kg, 
                    f->external_fuel_kg, f->max_external_fuel_kg};
        }
    }
    return {0.0, 0.0, 0.0, 0.0}; // Error/Not Found
}

std::vector<CommPacket> SimulationKernel::get_unit_messages(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const CommQueue* q = e.get<CommQueue>()) {
            return q->inbox;
        }
    }
    return {};
}

std::vector<UnitData> SimulationKernel::get_all_units() {
    std::vector<UnitData> units;

    auto query = ecs.query<const KeyEntity, const Transform, const Velocity, const Alliance>();
    query.each([&](flecs::entity e,
                   const KeyEntity& k,
                   const Transform& p,
                   const Velocity& /*v*/,
                   const Alliance& a) {
        UnitData data;
        data.id = e.id();
        data.side = static_cast<int>(a.side);
        data.type = static_cast<int>(k.type);
        data.x = p.x;
        data.y = p.y;
        data.z = p.z;
        data.heading = p.heading;
        units.push_back(data);
    });

    return units;
}

AgentObservation SimulationKernel::get_agent_observation(uint64_t entity_id) const {
    AgentObservation obs{};
    obs.id = entity_id;
    obs.sim_time = 0.0;
    obs.missiles_remaining = -1;
    obs.can_fire = false;
    obs.health = 0.0;
    obs.total_reward = 0.0;
    
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return obs; // Empty
    
    // Time
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    if (info) obs.sim_time = (double)info->world_time_total;
    
    // Self State
    const Transform* p = e.get<Transform>();
    const Velocity* v = e.get<Velocity>();
    const Health* h = e.get<Health>();
    
    // Safety Check: Transform is required for relative calculations (RWR)
    if (!p) return obs;

    if (p) {
        obs.x = p->x; obs.y = p->y; obs.z = p->z;
        obs.heading = p->heading; obs.pitch = p->pitch; obs.roll = p->roll;
    }
    if (v) {
        obs.vx = v->vx; obs.vy = v->vy; obs.vz = v->vz;
        obs.speed = std::sqrt(v->vx*v->vx + v->vy*v->vy + v->vz*v->vz);
    }
    if (h) {
        obs.health = h->current_hp;
    } else {
        obs.health = 0.0;
    }
    
    // Tracks (Fused Picture)
    const TrackDatabase* tracks = e.get<TrackDatabase>();
    if (tracks) {
         for (const auto& trk : tracks->tracks) {
             TrackData d;
             d.id = trk.track_id;
             d.range = trk.range;
             d.azimuth = trk.azimuth;
             d.elevation = trk.elevation;
             d.closing_speed = 0.0; // Not stored in SystemTrack yet, could be deriv
             d.time_since_update = trk.time_since_update;
             d.source = (int)trk.main_source;
             d.classification = (int)trk.classification;
             obs.contacts.push_back(d);
         }
    } else {
        // Fallback to raw sensor contacts
        const ContactList* c = e.get<ContactList>();
        if (c) {
            for (const auto& det : c->contacts) {
                TrackData track;
                track.id = det.target_id;
                track.range = det.range;
                track.time_since_update = obs.sim_time - det.timestamp;
                
                // Sensor already provides relative azimuth in NAV degrees.
                track.azimuth = det.bearing;
                track.elevation = det.elevation;
                track.closing_speed = det.closing_speed;
                track.source = 1; // Radar (Default)
                track.classification = 0; // Unknown
                
                obs.contacts.push_back(track);
            }
        }
    }
    
    // RWR Warnings (Electronic Warfare)
    const RWR* rwr = e.get<RWR>();
    if (rwr) {
        for (uint64_t source_id : rwr->detected_radar_ids) {
            // Retrieve source truth to simulate RWR processing
            // Note: In real life, RWR measures specific emitter parameters. 
            // Here we simulate the result of that measurement.
            auto source_e = ecs.entity(source_id);
            if (!source_e.is_valid()) continue;
            
            const Transform* source_t = source_e.get<Transform>();
            if (!source_t) continue;
            
            RWREvent event;
            event.source_id = source_id;
            
            // Calculate Bearing
            double dx = source_t->x - p->x;
            double dy = source_t->y - p->y;
            double bearing_rad = std::atan2(dy, dx);
            double bearing_math_deg = bearing_rad * 180.0 / M_PI;
            double bearing_nav_deg = 90.0 - bearing_math_deg; // Norm handled by simple math? 
            // 90 - (-170) = 260. Need wrap.
            if (bearing_nav_deg < 0) bearing_nav_deg += 360.0;
            if (bearing_nav_deg >= 360.0) bearing_nav_deg -= 360.0;
            
            double rel_bearing = bearing_nav_deg - p->heading;
            while (rel_bearing > 180.0) rel_bearing -= 360.0;
            while (rel_bearing < -180.0) rel_bearing += 360.0;
            
            event.bearing = rel_bearing; // Raw bearing for now (could add noise)
            
            // Signal Strength (1/R^2 approximation for RWR)
            double dist_sq = dx*dx + dy*dy;
            event.signal_strength = 1.0 / (dist_sq + 1.0); 
            
            event.signal_strength = 1.0 / (dist_sq + 1.0); 
            
            // Per-source Lock Check
            event.is_lock = false;
            for (auto lock_id : rwr->locking_radar_ids) {
                if (lock_id == source_id) {
                    event.is_lock = true;
                    break;
                }
            }
            // event.is_lock = rwr->is_locked; // Old global flag
            // For MVP, if *anyone* locks, we assume the strongest/all sources might be it?
            // Actually RWR struct needs IsLocked per source. 
            // Current struct: bool is_locked. 
            // So we just flag it.
            
            event.is_launch = rwr->is_missile_launch;
            
            obs.rwr_warnings.push_back(event);
        }
    }
    
    // Weapons check (Placeholder)
    const Ammo* ammo = e.get<Ammo>();
    const WeaponCooldown* cooldown = e.get<WeaponCooldown>();
    if (ammo) {
        obs.missiles_remaining = ammo->missiles_remaining;
        obs.can_fire = ammo->missiles_remaining > 0;
        if (obs.can_fire && cooldown && cooldown->cooldown_s > 0.0 && cooldown->last_fire_time >= 0.0) {
            obs.can_fire = (obs.sim_time - cooldown->last_fire_time) >= cooldown->cooldown_s;
        }
    } else {
        obs.missiles_remaining = -1;
        obs.can_fire = true;
    }
    
    const Score* s = e.get<Score>();
    obs.total_reward = s ? s->total_reward : 0.0;
    
    // System Status
    const LandingGear* gear = e.get<LandingGear>();
    obs.gear_state = gear ? gear->extension_state : 0.0;

    // Afterburner Visualization
    const InstrumentState* inst = e.get<InstrumentState>();
    if (inst) {
        // Normalize RPM. >100% usually means AB.
        // Assume 100% = MIL, 150% = Max AB roughly for viz scaling
        obs.throttle = inst->engine_rpm_pct / 100.0;
    } else {
        const Propulsion* prop = e.get<Propulsion>();
        if (prop && prop->mil_thrust_n > 0.1) {
             obs.throttle = prop->current_thrust_n / prop->mil_thrust_n;
             if (prop->afterburner_active) obs.throttle = 1.5; 
        } else {
             obs.throttle = 0.0;
        }
    }
    
    return obs;
}
