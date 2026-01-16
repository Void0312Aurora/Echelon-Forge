#pragma once

#include <memory>

#include <flecs.h>

#include "components/common.h"
#include "components/sensor.h"

class ISensorModel {
public:
    virtual ~ISensorModel() = default;

    virtual void scan(flecs::world world,
                      flecs::entity owner,
                      const Transform& owner_transform,
                      const Sensor& sensor,
                      ContactList& out_contacts,
                      double current_time) = 0;
};

struct SensorModelRef {
    ISensorModel* model;
};

std::unique_ptr<ISensorModel> make_default_sensor_model();
