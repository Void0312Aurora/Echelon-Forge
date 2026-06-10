#include "simulation_kernel.h"
#include "simulation_kernel_engagement_event_store.h"

#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/physics/dynamics.h"
#include "components/physics/instruments.h"
#include "components/physics/performance.h"
#include "components/systems/ew.h"
#include "components/systems/data_link.h"
#include "components/systems/logistics.h"
#include "components/systems/navigation.h"
#include "components/systems/sensor.h"
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"
#include "components/domains/naval/platform/embarked_air_ops.h"

#include <spdlog/spdlog.h>

#include <cmath>
#include <algorithm>
#include <limits>
#include <vector>

namespace {

TrackClass classify_observation_contact(const Alliance *owner_alliance,
                                        const Alliance *target_alliance) {
    if (!owner_alliance || !target_alliance) {
        return TrackClass::Unknown;
    }
    if (target_alliance->side == Side::Neutral || target_alliance->side == Side::Unknown) {
        return TrackClass::Neutral;
    }
    return owner_alliance->side == target_alliance->side ? TrackClass::Friendly
                                                         : TrackClass::Hostile;
}

} // namespace

std::vector<double> SimulationKernel::get_unit_position(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Transform *t = e.get<Transform>();
        if (t) {
            return {t->x, t->y, t->z};
        }
    }
    return {0.0, 0.0, 0.0};
}

RecentEngagementEvents SimulationKernel::export_recent_engagement_events() const {
    return engagement_event_store_->export_recent_events_sorted();
}

std::vector<double> SimulationKernel::get_unit_velocity(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Velocity *v = e.get<Velocity>();
        if (v) {
            return {v->vx, v->vy, v->vz};
        }
    }
    return {0.0, 0.0, 0.0};
}

double SimulationKernel::get_unit_heading(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return 0.0;
    }

    if (const Transform *t = e.get<Transform>()) {
        return t->heading;
    }

    const Velocity *v = e.get<Velocity>();
    if (!v) {
        return 0.0;
    }

    double math_rad = std::atan2(v->vy, v->vx);
    double math_deg = math_rad * 180.0 / M_PI;
    double nav_deg = 90.0 - math_deg;
    while (nav_deg < 0.0)
        nav_deg += 360.0;
    while (nav_deg >= 360.0)
        nav_deg -= 360.0;
    return nav_deg;
}

std::vector<Detection> SimulationKernel::get_detections(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList *c = e.get<ContactList>();
        if (c) {
            return c->contacts;
        }
    }
    return {};
}

InstrumentState SimulationKernel::get_instrument_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const InstrumentState *inst = e.get<InstrumentState>()) {
            return *inst;
        }
    }
    return InstrumentState{};
}

EGI SimulationKernel::get_egi_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const EGI *egi = e.get<EGI>()) {
            return *egi;
        }
    }
    return EGI{};
}

int SimulationKernel::get_unit_type(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return 0;
    }

    const KeyEntity *key = e.get<KeyEntity>();
    return key ? static_cast<int>(key->type) : 0;
}

bool SimulationKernel::is_unit_active(uint64_t entity_id) {
    return ecs.entity(entity_id).is_valid();
}

void SimulationKernel::set_contact_list(uint64_t entity_id,
                                        const std::vector<Detection> &detections) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        ContactList contacts{};
        contacts.contacts = detections;
        const ecs_world_info_t *info = ecs_get_world_info(ecs.c_ptr());
        const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
        const double injected_time = current_time + time_step;
        for (auto &det : contacts.contacts) {
            if (det.timestamp <= current_time + 1.0e-6) {
                det.timestamp = injected_time;
            }
        }
        e.set<ContactList>(contacts);
    } else {
        spdlog::warn("Attempted to set contact list for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_unit_ammo(uint64_t entity_id, int missiles_remaining, int max_missiles) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        spdlog::warn("Attempted to set ammo for invalid entity ID: {}", entity_id);
        return;
    }
    const int remaining = std::max(0, missiles_remaining);
    const int maximum = std::max(remaining, std::max(0, max_missiles));
    e.set<Ammo>({remaining, maximum});
}

void SimulationKernel::set_weapon_cooldown(uint64_t entity_id, double cooldown_s,
                                           double last_fire_time) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        spdlog::warn("Attempted to set weapon cooldown for invalid entity ID: {}", entity_id);
        return;
    }
    e.set<WeaponCooldown>({cooldown_s, last_fire_time});
}

double SimulationKernel::debug_get_last_scan_time(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const Sensor *s = e.get<Sensor>();
        if (s) return s->last_scan_time;
        const Sonar *sonar = e.get<Sonar>();
        if (sonar) return sonar->last_scan_time_s;
    }
    return std::numeric_limits<double>::quiet_NaN();
}

int SimulationKernel::debug_get_contact_count(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ContactList *c = e.get<ContactList>();
        if (c) return static_cast<int>(c->contacts.size());
    }
    return -1;
}

std::vector<double> SimulationKernel::debug_get_mass_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {};

    const Mass *mass = e.get<Mass>();
    const MassProperties *props = e.get<MassProperties>();
    if (!mass || !props) return {};

    return {
        mass->empty_mass_kg,  mass->fuel_mass_kg,   mass->stores_mass_kg,
        mass->get_total_kg(), props->empty_mass_kg, props->current_total_mass_kg,
    };
}

std::vector<double> SimulationKernel::get_unit_health(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {0.0, 0.0};

    if (const Health *h = e.get<Health>()) {
        return {h->current_hp, h->max_hp};
    }
    return {0.0, 0.0};
}

std::vector<double> SimulationKernel::get_unit_damage_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {0.0, 0.0, 0.0, 0.0};

    if (const PlatformDamageState *state = e.get<PlatformDamageState>()) {
        return {
            state->mission_capability,
            state->mobility_capability,
            state->sensor_capability,
            state->survivability_margin,
        };
    }
    return {1.0, 1.0, 1.0, 1.0};
}

std::vector<double> SimulationKernel::debug_get_aircraft_damage_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return {};
    }

    if (const AircraftDamageState *state = e.get<AircraftDamageState>()) {
        return {
            state->structural_integrity,
            state->flight_control_integrity,
            state->hydraulic_integrity,
            state->hydraulic_pressure_availability,
            state->roll_control_integrity,
            state->pitch_control_integrity,
            state->yaw_control_integrity,
            state->control_asymmetry,
            state->propulsion_integrity,
            state->fuel_system_integrity,
            state->avionics_integrity,
            state->crew_effectiveness,
            state->pilot_effectiveness,
            state->mission_crew_effectiveness,
            state->command_navigation_integrity,
            state->fire_severity,
            state->fuel_leak_severity,
            state->fuel_imbalance_severity,
            state->flammable_fluid_exposure,
            state->ignition_source_severity,
            state->fire_suppression_integrity,
            state->smoke_heat_exposure,
            state->engine_fire_zone_severity,
            state->wing_fire_zone_severity,
            state->fuselage_fire_zone_severity,
            state->mission_fire_zone_severity,
            state->structural_overstress,
            state->flutter_exposure,
            state->forced_landing_required ? 1.0 : 0.0,
            state->flight_control_kill ? 1.0 : 0.0,
            state->propulsion_kill ? 1.0 : 0.0,
            state->crew_kill ? 1.0 : 0.0,
        };
    }
    return {};
}

std::vector<double>
SimulationKernel::debug_get_aircraft_vulnerability_evidence_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return {};
    }

    const AircraftVulnerabilityProfile *profile = e.get<AircraftVulnerabilityProfile>();
    if (!profile) {
        return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    }
    return {
        1.0,
        profile->synthetic ? 1.0 : 0.0,
        aircraft_vulnerability_has_calibrated_evidence(*profile) ? 1.0 : 0.0,
        aircraft_vulnerability_pk_authority(*profile) ? 1.0 : 0.0,
        aircraft_vulnerability_deterministic_fuze_authority(*profile) ? 1.0 : 0.0,
        profile->evidence_dataset_valid ? 1.0 : 0.0,
    };
}

std::vector<double>
SimulationKernel::debug_get_aircraft_vulnerability_authority_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return {};
    }

    const AircraftVulnerabilityProfile *profile = e.get<AircraftVulnerabilityProfile>();
    if (!profile) {
        return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    }
    return {
        1.0,
        profile->synthetic ? 1.0 : 0.0,
        aircraft_vulnerability_has_calibrated_evidence(*profile) ? 1.0 : 0.0,
        profile->effect_scale_authority ? 1.0 : 0.0,
        profile->component_failure_probability_authority ? 1.0 : 0.0,
        aircraft_vulnerability_pk_authority(*profile) ? 1.0 : 0.0,
        aircraft_vulnerability_deterministic_fuze_authority(*profile) ? 1.0 : 0.0,
        profile->evidence_dataset_valid ? 1.0 : 0.0,
    };
}

std::vector<double> SimulationKernel::debug_get_naval_weapon_counts(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return {};

    const NavalWeaponSystem *system = e.get<NavalWeaponSystem>();
    if (!system) return {};

    double ready_vls = 0.0;
    double ready_gun = 0.0;
    double ready_ciws = 0.0;
    for (const auto &mount : system->mounts) {
        if (mount.weapon_type == NavalWeaponType::VlsSam)
            ready_vls += mount.ready_count;
        else if (mount.weapon_type == NavalWeaponType::DeckGun)
            ready_gun += mount.ready_count;
        else if (mount.weapon_type == NavalWeaponType::Ciws)
            ready_ciws += mount.ready_count;
    }
    return {
        static_cast<double>(system->mounts.size()),
        ready_vls,
        ready_gun,
        ready_ciws,
    };
}

std::vector<double> SimulationKernel::get_unit_fuel(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const FuelSystem *f = e.get<FuelSystem>()) {
            return {f->internal_fuel_kg, f->max_internal_fuel_kg, f->external_fuel_kg,
                    f->max_external_fuel_kg};
        }
    }
    return {0.0, 0.0, 0.0, 0.0}; // Error/Not Found
}

std::vector<double> SimulationKernel::debug_get_naval_stores(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const NavalStores *stores = e.get<NavalStores>()) {
            return {
                stores->fuel_units_current,      stores->fuel_units_max,
                stores->missile_units_current,   stores->missile_units_max,
                stores->dry_cargo_units_current, stores->dry_cargo_units_max,
            };
        }
    }
    return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
}

std::vector<double> SimulationKernel::debug_get_logistics_node(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const LogisticsNode *node = e.get<LogisticsNode>()) {
            return {
                node->supply_radius_m,
                node->infinite_supply ? 1.0 : 0.0,
                node->underway_replenishment_enabled ? 1.0 : 0.0,
                node->underway_min_separation_m,
                node->underway_max_separation_m,
                node->underway_max_relative_speed_mps,
                node->transfer_rate_fuel_units_per_s,
                node->transfer_rate_missile_units_per_s,
                node->transfer_rate_dry_cargo_units_per_s,
            };
        }
    }
    return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
}

std::vector<double> SimulationKernel::debug_get_resupply_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const ResupplyState *state = e.get<ResupplyState>()) {
            const bool active =
                (state->kind == ResupplyKind::NavalUnderway &&
                 state->naval_stage == NavalResupplyStage::Transferring) ||
                (state->kind == ResupplyKind::BaseRefuel && state->time_remaining_s > 0.0 &&
                 (state->is_refueling || state->is_rearming));
            return {
                active ? 1.0 : 0.0,
                static_cast<double>(state->kind),
                static_cast<double>(state->partner_entity_id),
                static_cast<double>(state->naval_stage),
                state->time_remaining_s,
                state->is_refueling ? 1.0 : 0.0,
                state->is_rearming ? 1.0 : 0.0,
            };
        }
    }
    return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
}

std::vector<double> SimulationKernel::debug_get_data_link_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const DataLink *link = e.get<DataLink>()) {
            return {
                static_cast<double>(link->max_reports_per_update),
                static_cast<double>(link->max_messages_per_update),
                static_cast<double>(link->reports_sent_last_update),
                static_cast<double>(link->messages_sent_last_update),
                static_cast<double>(link->reports_dropped_last_update),
                static_cast<double>(link->messages_dropped_last_update),
                static_cast<double>(link->reports_sent_total),
                static_cast<double>(link->messages_sent_total),
                static_cast<double>(link->reports_dropped_total),
                static_cast<double>(link->messages_dropped_total),
            };
        }
    }
    return {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
}

std::vector<double> SimulationKernel::debug_get_ground_contact_state(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        return {};
    }

    const GroundState *ground = e.get<GroundState>();
    const GearState *gear = e.get<GearState>();
    if (!ground) {
        return {};
    }

    return {
        ground->on_ground ? 1.0 : 0.0,
        ground->terrain_elevation,
        static_cast<double>(ground->lifecycle),
        ground->impact_horizontal_speed_mps,
        ground->impact_sink_rate_mps,
        ground->impact_severity,
        gear ? gear->stress : 0.0,
        (gear && gear->collapsed) ? 1.0 : 0.0,
        (!gear || gear->on_runway) ? 1.0 : 0.0,
    };
}

std::vector<CommPacket> SimulationKernel::get_unit_messages(uint64_t entity_id) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const CommQueue *q = e.get<CommQueue>()) {
            return q->inbox;
        }
    }
    return {};
}

std::uint64_t SimulationKernel::debug_get_embarked_helo(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const EmbarkedAirOps *ops = e.get<EmbarkedAirOps>()) {
            return ops->active_helo_entity_id;
        }
    }
    return 0;
}

std::vector<UnitData> SimulationKernel::get_all_units() {
    std::vector<UnitData> units;

    auto query = ecs.query<const KeyEntity, const Transform, const Velocity, const Alliance>();
    query.each([&](flecs::entity e, const KeyEntity &k, const Transform &p, const Velocity & /*v*/,
                   const Alliance &a) {
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
    const ecs_world_info_t *info = ecs_get_world_info(ecs.c_ptr());
    if (info) obs.sim_time = (double)info->world_time_total;

    // Self State
    const Transform *p = e.get<Transform>();
    const Velocity *v = e.get<Velocity>();
    const Health *h = e.get<Health>();

    // Safety Check: Transform is required for relative calculations (RWR)
    if (!p) return obs;

    if (p) {
        obs.x = p->x;
        obs.y = p->y;
        obs.z = p->z;
        obs.heading = p->heading;
        obs.pitch = p->pitch;
        obs.roll = p->roll;
    }
    if (v) {
        obs.vx = v->vx;
        obs.vy = v->vy;
        obs.vz = v->vz;
        obs.speed = std::sqrt(v->vx * v->vx + v->vy * v->vy + v->vz * v->vz);
    }
    if (h) {
        obs.health = h->current_hp;
    } else {
        obs.health = 0.0;
    }

    // Tracks (Fused Picture)
    const TrackDatabase *tracks = e.get<TrackDatabase>();
    if (tracks && !tracks->tracks.empty()) {
        for (const auto &trk : tracks->tracks) {
            TrackData d;
            d.id = trk.track_id;
            d.range = trk.range;
            d.azimuth = trk.azimuth;
            d.elevation = trk.elevation;
            d.closing_speed = 0.0;
            const double dx = trk.x - p->x;
            const double dy = trk.y - p->y;
            const double dz = trk.z - p->z;
            const double dist_sq = dx * dx + dy * dy + dz * dz;
            if (dist_sq > 1.0e-6) {
                const double dist = std::sqrt(dist_sq);
                const double rx = dx / dist;
                const double ry = dy / dist;
                const double rz = dz / dist;
                const double rel_vx = trk.vx - obs.vx;
                const double rel_vy = trk.vy - obs.vy;
                const double rel_vz = trk.vz - obs.vz;
                d.closing_speed = -(rel_vx * rx + rel_vy * ry + rel_vz * rz);
            }
            d.time_since_update = trk.time_since_update;
            d.source = (int)trk.main_source;
            d.classification = (int)trk.classification;
            d.status = (int)trk.status;
            d.quality = trk.quality;
            d.confidence = trk.confidence;
            d.usability = (int)track_usability_for(trk);
            d.iff_known = trk.iff_known;
            d.classification_confidence = trk.classification_confidence;
            obs.contacts.push_back(d);
        }
    } else {
        // Fallback to raw sensor contacts
        const ContactList *c = e.get<ContactList>();
        const Alliance *owner_alliance = e.get<Alliance>();
        if (c) {
            for (const auto &det : c->contacts) {
                TrackData track;
                track.id = det.target_id;
                track.range = det.range;
                track.time_since_update = obs.sim_time - det.timestamp;

                // Sensor already provides relative azimuth in NAV degrees.
                track.azimuth = det.bearing;
                track.elevation = det.elevation;
                track.closing_speed = det.closing_speed;
                if (det.sensor_type == static_cast<int>(SensorType::ESM) || det.range <= 0.0) {
                    track.source = 2; // Passive / bearing-only
                } else if (det.sensor_type == static_cast<int>(SensorType::Sonar)) {
                    track.source = 5; // Sonar
                } else {
                    track.source = 1; // Radar (Default)
                }
                const Alliance *target_alliance = ecs.entity(det.target_id).get<Alliance>();
                track.classification =
                    static_cast<int>(classify_observation_contact(owner_alliance, target_alliance));
                track.status = 0; // Tentative
                const double fallback_confidence =
                    det.detection_prob_used > 0.0 ? det.detection_prob_used : 0.25;
                track.quality = fallback_confidence;
                track.confidence = fallback_confidence;
                track.usability = 0; // None
                track.iff_known = false;
                track.classification_confidence = 0.0;

                obs.contacts.push_back(track);
            }
        }
    }

    // RWR Warnings (Electronic Warfare)
    const RWR *rwr = e.get<RWR>();
    if (rwr) {
        for (uint64_t source_id : rwr->detected_radar_ids) {
            // Retrieve source truth to simulate RWR processing
            // Note: In real life, RWR measures specific emitter parameters.
            // Here we simulate the result of that measurement.
            auto source_e = ecs.entity(source_id);
            if (!source_e.is_valid()) continue;

            const Transform *source_t = source_e.get<Transform>();
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
            while (rel_bearing > 180.0)
                rel_bearing -= 360.0;
            while (rel_bearing < -180.0)
                rel_bearing += 360.0;

            event.bearing = rel_bearing; // Raw bearing for now (could add noise)

            // Signal Strength (1/R^2 approximation for RWR)
            double dist_sq = dx * dx + dy * dy;
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

    const ESMReceiver *esm = e.get<ESMReceiver>();
    if (esm) {
        for (const auto &det : esm->detections) {
            RWREvent event{};
            event.source_id = det.source_id;
            event.bearing = det.bearing_deg;
            event.signal_strength = det.signal_strength;
            event.is_lock = det.is_radar_lock;
            event.is_launch = det.is_missile_guidance;
            obs.rwr_warnings.push_back(event);
        }
    }

    // Weapons check (Placeholder)
    const Ammo *ammo = e.get<Ammo>();
    const WeaponCooldown *cooldown = e.get<WeaponCooldown>();
    if (ammo) {
        obs.missiles_remaining = ammo->missiles_remaining;
        obs.can_fire = ammo->missiles_remaining > 0;
        if (obs.can_fire && cooldown && cooldown->cooldown_s > 0.0 &&
            cooldown->last_fire_time >= 0.0) {
            obs.can_fire = (obs.sim_time - cooldown->last_fire_time) >= cooldown->cooldown_s;
        }
    } else {
        obs.missiles_remaining = -1;
        obs.can_fire = true;
    }

    const Score *s = e.get<Score>();
    obs.total_reward = s ? s->total_reward : 0.0;

    // System Status
    const LandingGear *gear = e.get<LandingGear>();
    obs.gear_state = gear ? gear->extension_state : 0.0;

    // Propulsion readout: prefer actual spool/AB state over RPM-derived heuristics.
    const Propulsion *prop = e.get<Propulsion>();
    if (prop) {
        const double throttle_state = std::clamp(prop->throttle_state, 0.0, 1.0);
        const double ab_state = std::clamp(prop->ab_state, 0.0, 1.0);
        obs.throttle = throttle_state + (0.5 * ab_state);
    } else {
        const InstrumentState *inst = e.get<InstrumentState>();
        if (inst) {
            obs.throttle = std::clamp(inst->engine_rpm_pct / 100.0, 0.0, 1.5);
        } else {
            obs.throttle = 0.0;
        }
    }

    return obs;
}
