#pragma once

#include <memory>

#include <flecs.h>

#include "components/basic/common.h"
#include "components/systems/sensor.h"
#include "components/systems/sonar.h"

class IAcousticModel {
public:
    virtual ~IAcousticModel() = default;

    virtual void scan(flecs::world world,
                      flecs::entity owner,
                      const Transform& owner_transform,
                      const Sonar& sonar,
                      ContactList& out_contacts,
                      double current_time) = 0;
};

struct AcousticModelRef {
    IAcousticModel* model = nullptr;
};

std::unique_ptr<IAcousticModel> make_default_acoustic_model();
