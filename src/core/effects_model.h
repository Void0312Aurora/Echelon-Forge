#pragma once

#include <memory>

#include <flecs.h>

#include "components/weapon.h"

struct EffectsResult {
    bool destroy_missile = true;
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
