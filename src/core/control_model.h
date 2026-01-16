#pragma once

#include <memory>

#include <flecs.h>

#include "components/action.h"
#include "components/common.h"
#include "components/performance.h"

class IControlModel {
public:
    virtual ~IControlModel() = default;

    virtual void update(flecs::world world,
                        flecs::entity entity,
                        Velocity& velocity,
                        Transform& transform,
                        const MovementCommand& command,
                        const FlightModel& flight_model,
                        double dt) = 0;
};

struct ControlModelRef {
    IControlModel* model;
};

std::unique_ptr<IControlModel> make_default_control_model();
