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
    instrument.countermeasure_snapshot_stage = 31;
    instrument.countermeasure_snapshot_time_s = current_time;
    instrument.countermeasure_snapshot_post_ew = true;
}

inline void project_jammer_instrument(InstrumentState &instrument, const Jammer *jammer) {
    if (jammer && jammer_installed(*jammer)) {
        instrument.jammer_transmitting = jammer->is_active;
        instrument.jammer_mode = static_cast<int>(jammer->type);
        instrument.jammer_transmit_start_time_s = jammer->transmit_start_time_s;
    } else {
        instrument.jammer_transmitting = false;
        instrument.jammer_mode = -1;
        instrument.jammer_transmit_start_time_s = -1.0;
    }
}

inline void register_ew_system(flecs::world &ecs) {
    // 0. Self-protection jammer command owner. It runs inside the EW node
    // before the dispensers, so the radar scan of the next frame (SensorSystem
    // precedes EW in the OnUpdate order) sees the admitted transmit state. An
    // active PilotAction is the cockpit switch state; without one the suite's
    // database state holds.
    ecs.system<Jammer, InstrumentState>("EW_Jammer_Control").run([](flecs::iter &it) {
        while (it.next()) {
            auto jammer = it.field<Jammer>(0);
            auto instrument = it.field<InstrumentState>(1);
            const ecs_world_info_t *info = ecs_get_world_info(it.world().c_ptr());
            const double current_time = info ? (double)info->world_time_total : 0.0;
            for (auto i : it) {
                const ResolvedJammerCommand command = resolve_jammer_command(it.entity(i));
                if (command.commanded) {
                    apply_jammer_command(jammer[i], command.transmit, command.mode_code,
                                         current_time);
                } else if (jammer[i].is_active && jammer[i].transmit_start_time_s < 0.0 &&
                           jammer_installed(jammer[i])) {
                    // Database-initialised transmit state: stamp its start.
                    jammer[i].transmit_start_time_s = current_time;
                }
                project_jammer_instrument(instrument[i], &jammer[i]);
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
                            auto chaff = it.world().entity();
                            chaff.set<Transform>({p[i].x, p[i].y, p[i].z, 0.0, 0.0, 0.0})
                                .set<Velocity>({v[i].vx * 0.1, v[i].vy * 0.1, v[i].vz * 0.1})
                                .set<RCSProfile>({50.0, 50.0, 50.0})
                                .set<Lifetime>({20.0, 0.0})
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
                                .set<Lifetime>({10.0, 0.0})
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
