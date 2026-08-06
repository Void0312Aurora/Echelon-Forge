#pragma once

#include <memory>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/physics/performance.h"
#include "core/interfaces/environment_model.h"

class IControlModel {
  public:
    virtual ~IControlModel() = default;

    virtual void update(flecs::world world, flecs::entity entity, Velocity &velocity,
                        Transform &transform, const FlightModel &flight_model, double dt,
                        IEnvironmentModel *env_model = nullptr) = 0;
};

struct ControlModelRef {
    IControlModel *model;
};

std::unique_ptr<IControlModel> make_default_control_model();
