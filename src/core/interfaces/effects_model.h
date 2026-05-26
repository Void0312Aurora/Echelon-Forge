#pragma once

#include <cstdint>
#include <memory>
#include <string>

#include <flecs.h>

#include "components/combat/weapon.h"

struct EffectsResult {
    bool destroy_missile = true;
    bool direct_hitbox_intersection = false;
    std::uint32_t projected_hitbox_count = 0;
    double spatial_effect_scale = 0.0;
    double mechanism_armor_scale = 1.0;
    double mechanism_exposure_scale = 1.0;
    double mechanism_effect_scale = 1.0;
    double component_threshold_scale = 1.0;
    double component_failure_probability = 0.0;
    double component_failure_sample = 1.0;
    std::uint32_t component_failure_count = 0;
    std::uint32_t component_hit_count = 0;
    std::string component_primary_name;
    std::string component_primary_system;
    double component_primary_redundancy_group = 0.0;
    bool component_primary_critical = false;
};

class IEffectsModel {
public:
    virtual ~IEffectsModel() = default;

    virtual EffectsResult on_proximity_hit(flecs::world world,
                                           flecs::entity missile_entity,
                                           const Missile& missile,
                                           flecs::entity target_entity) = 0;
};

struct EffectsModelRef {
    IEffectsModel* model;
};

std::unique_ptr<IEffectsModel> make_default_effects_model();
