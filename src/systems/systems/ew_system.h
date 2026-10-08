#pragma once

#include <flecs.h>
#include <spdlog/spdlog.h>
#include "components/basic/common.h"
#include "components/basic/tags.h"
#include "core/interfaces/stable_entity_identity.h"
#include "components/command/legacy_command_bridge.h"
#include "components/physics/instruments.h"
#include "components/systems/ew.h"

inline void project_countermeasure_instrument(InstrumentState &instrument,
                                              const Countermeasures &cm, double current_time) {
    instrument.countermeasure_chaff_remaining = cm.chaff_count;
    instrument.countermeasure_flare_remaining = cm.flare_count;
    instrument.countermeasure_release_interval_s = cm.release_interval;
    instrument.countermeasure_last_release_time_s = cm.last_release_time;
    instrument.countermeasure_auto_mode = cm.auto_mode;
    instrument.set_countermeasure_snapshot_producer(
        CountermeasureSnapshotProducer::CountermeasureReleaseProjection, current_time);
}

inline void project_jammer_instrument(InstrumentState &instrument, const Jammer *jammer,
                                      double current_time = -1.0) {
    if (jammer && jammer_installed(*jammer)) {
        instrument.jammer_transmitting = jammer->is_active;
        instrument.jammer_mode = static_cast<int>(jammer->type);
        instrument.jammer_transmit_start_time_s = jammer->transmit_start_time_s;
        instrument.jammer_budget_enabled = jammer_budget_enabled(*jammer);
        instrument.jammer_transmit_remaining_s =
            instrument.jammer_budget_enabled
                ? std::max(0.0, jammer->max_continuous_transmit_s - jammer->transmit_elapsed_s)
                : -1.0;
        instrument.jammer_cooldown_remaining_s =
            instrument.jammer_budget_enabled
                ? std::max(0.0, jammer->cooldown_until_time_s - current_time)
                : -1.0;
        instrument.jammer_snapshot_time_s = current_time;
    } else {
        instrument.jammer_transmitting = false;
        instrument.jammer_mode = -1;
        instrument.jammer_transmit_start_time_s = -1.0;
        instrument.jammer_budget_enabled = false;
        instrument.jammer_transmit_remaining_s = -1.0;
        instrument.jammer_cooldown_remaining_s = -1.0;
        instrument.jammer_snapshot_time_s = current_time;
    }
}

inline void register_ew_system(flecs::world &ecs) {
    ecs.system<Jammer>("EW_Jammer_Control").run([](flecs::iter &it) {
        while (it.next()) {
            auto jammer = it.field<Jammer>(0);
            const ecs_world_info_t *info = ecs_get_world_info(it.world().c_ptr());
            const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
            for (auto i : it) {
                advance_jammer_budget(jammer[i], current_time);
                const ResolvedJammerCommand command = resolve_jammer_command(it.entity(i));
                if (command.commanded) {
                    apply_jammer_command(jammer[i], command.transmit, command.mode_code,
                                         current_time);
                } else if (jammer[i].is_active && jammer[i].transmit_start_time_s < 0.0 &&
                           jammer_installed(jammer[i])) {
                    jammer[i].transmit_start_time_s = current_time;
                }
                if (auto *instrument = it.entity(i).get_mut<InstrumentState>()) {
                    project_jammer_instrument(*instrument, &jammer[i], current_time);
                }
            }
        }
    });

    // 1. Chaff Release System
    ecs.system<Countermeasures, InstrumentState, const Transform, const Velocity>(
           "EW_Release_Chaff")
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto cm = it.field<Countermeasures>(0);
                auto instrument = it.field<InstrumentState>(1);
                auto p = it.field<const Transform>(2);
                auto v = it.field<const Velocity>(3);

                const ecs_world_info_t *info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    const auto command = resolve_compatibility_countermeasure_command(it.entity(i));
                    if (command.release_chaff) {
                        if (cm[i].chaff_count > 0 &&
                            countermeasure_release_ready(cm[i].last_chaff_release_time,
                                                         cm[i].release_interval, current_time)) {
                            cm[i].chaff_count--;
                            cm[i].last_release_time = current_time;
                            cm[i].last_chaff_release_time = current_time;

                            // Spawn Chaff Entity
                            // Creation is deferred inside this system; the stamp advances
                            // the live identity counter immediately, in iteration order.
                            const double chaff_rcs =
                                countermeasure_positive_or(cm[i].chaff_rcs_m2, kDefaultChaffRcsM2);
                            auto chaff = it.world().entity();
                            chaff.set<Transform>({p[i].x, p[i].y, p[i].z, 0.0, 0.0, 0.0})
                                .set<Velocity>({v[i].vx * 0.1, v[i].vy * 0.1, v[i].vz * 0.1})
                                .set<RCSProfile>({chaff_rcs, chaff_rcs, chaff_rcs})
                                .set<Lifetime>({countermeasure_positive_or(cm[i].chaff_lifetime_s,
                                                                           kDefaultChaffLifetimeS),
                                                0.0})
                                .set<Decoy>({DecoyKind::Chaff,
                                             static_cast<std::uint64_t>(it.entity(i).id()),
                                             current_time, chaff_rcs})
                                .set<KeyEntity>({UnitType::Unknown})
                                .add<SimObject>();
                            stamp_stable_serial(chaff);

                            spdlog::debug("Unit {} released Chaff. Remaining: {}",
                                          it.entity(i).id(), cm[i].chaff_count);
                        }
                        project_countermeasure_instrument(instrument[i], cm[i], current_time);
                    }
                }
            }
        });

    // 2. Flare Release System
    ecs.system<Countermeasures, InstrumentState, const Transform, const Velocity>(
           "EW_Release_Flare")
        .run([](flecs::iter &it) {
            while (it.next()) {
                auto cm = it.field<Countermeasures>(0);
                auto instrument = it.field<InstrumentState>(1);
                auto p = it.field<const Transform>(2);
                auto v = it.field<const Velocity>(3);

                const ecs_world_info_t *info = ecs_get_world_info(it.world().c_ptr());
                double current_time = info ? (double)info->world_time_total : 0.0;

                for (auto i : it) {
                    const auto command = resolve_compatibility_countermeasure_command(it.entity(i));
                    if (command.release_flare) {
                        if (cm[i].flare_count > 0 &&
                            countermeasure_release_ready(cm[i].last_flare_release_time,
                                                         cm[i].release_interval, current_time)) {
                            cm[i].flare_count--;
                            cm[i].last_release_time = current_time;
                            cm[i].last_flare_release_time = current_time;

                            auto flare = it.world().entity();
                            flare.set<Transform>({p[i].x, p[i].y, p[i].z, 0.0, 0.0, 0.0})
                                .set<Velocity>({v[i].vx, v[i].vy, v[i].vz})
                                .set<Lifetime>({countermeasure_positive_or(cm[i].flare_lifetime_s,
                                                                           kDefaultFlareLifetimeS),
                                                0.0})
                                .set<Decoy>({DecoyKind::Flare,
                                             static_cast<std::uint64_t>(it.entity(i).id()),
                                             current_time,
                                             countermeasure_positive_or(cm[i].flare_ir_intensity,
                                                                        kDefaultFlareIrIntensity)})
                                .set<KeyEntity>({UnitType::Unknown})
                                .add<SimObject>();
                            stamp_stable_serial(flare);

                            spdlog::debug("Unit {} released Flare. Remaining: {}",
                                          it.entity(i).id(), cm[i].flare_count);
                        }
                        project_countermeasure_instrument(instrument[i], cm[i], current_time);
                    }
                }
            }
        });

    // 3. Lifetime Management System
    ecs.system<Lifetime>("EW_Lifetime_Manager").run([](flecs::iter &it) {
        while (it.next()) {
            auto l = it.field<Lifetime>(0);
            double dt = it.delta_time();

            for (auto i : it) {
                l[i].current_age += dt;
                if (l[i].current_age > l[i].max_age) {
                    it.entity(i).destruct();
                }
            }
        }
    });
}
