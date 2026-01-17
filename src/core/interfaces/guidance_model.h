#pragma once

#include <memory>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/combat/weapon.h"

class IGuidanceModel {
public:
    virtual ~IGuidanceModel() = default;

    virtual void update(flecs::world world,
                        flecs::entity missile_entity,
                        Velocity& velocity,
                        const Transform& transform,
                        Missile& missile,
                        double dt) = 0;
};

struct GuidanceModelRef {
    IGuidanceModel* model;
};

std::unique_ptr<IGuidanceModel> make_default_guidance_model();
