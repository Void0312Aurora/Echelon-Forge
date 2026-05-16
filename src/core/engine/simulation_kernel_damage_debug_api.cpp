#include "simulation_kernel.h"

#include "components/basic/common.h"
#include "components/combat/weapon.h"
#include "core/interfaces/effects_model.h"

#include <limits>

bool SimulationKernel::debug_apply_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double damage,
    double fuse_distance
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    auto impact = ecs.entity()
        .set<Transform>({
            target_transform->x,
            target_transform->y,
            target_transform->z + 2.0,
            target_transform->heading,
            0.0,
            0.0,
        })
        .set<Missile>(synthetic)
        .add<SimObject>();

    effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    impact.destruct();
    return true;
}
