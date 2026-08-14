// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

bool apply_legacy_health_damage(flecs::entity target_entity, const Missile &missile, Score *score,
                                Health &hp) {
    hp.current_hp -= missile.damage;
    if (score) {
        score->total_reward += missile.damage;
        score->hits_landed++;
    }

    if (hp.current_hp > 0) {
        return false;
    }

    target_entity.destruct();
    if (score) {
        score->total_reward += 1000.0;
        score->kills_confirmed++;
    }
    spdlog::info("SPLASH! Target {} Destroyed.", target_entity.id());
    return true;
}

void apply_legacy_randomized_fallback_effects(flecs::entity missile_entity,
                                              flecs::entity target_entity, const Missile &missile,
                                              const Health *hp) {
    double severity = 0.5;
    if (hp && hp->max_hp > 0) {
        severity = missile.damage / hp->max_hp;
    }

    const double p = std::clamp(0.3 + 0.5 * severity, 0.0, 1.0);
    uint64_t rng_state = missile.rng_state;
    const double u = rand_uniform01(rng_state);
    if (u < p) {
        if (Sensor *sensor = target_entity.get_mut<Sensor>()) {
            sensor->max_range *= 0.5;
        }
    }
    if (Missile *mutable_missile = missile_entity.get_mut<Missile>()) {
        mutable_missile->rng_state = rng_state;
    }
}
