#pragma once

#include <cstdint>
#include <string>

#include <flecs.h>

#include "components/common.h"
#include "content/unit_definition.h"

struct SpawnParams {
    Side side;
    double x, y, z;
    double vx, vy, vz;
};

class IUnitFactory {
public:
    virtual ~IUnitFactory() = default;

    virtual const UnitDefinition* get_definition(UnitType type) const = 0;
    virtual flecs::entity spawn(flecs::world& ecs,
                                const UnitDefinition& def,
                                const SpawnParams& params) = 0;

    virtual bool load_definitions(const std::string& /*path*/,
                                  std::string* error) {
        if (error) *error = "UnitFactory does not support loading definitions.";
        return false;
    }
};
