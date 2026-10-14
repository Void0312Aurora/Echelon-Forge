#pragma once

#include <cstdint>
#include <string>
#include <string_view>

#include <flecs.h>

#include "components/basic/common.h"
#include "content/unit_definition.h"
#include "runtime/contracts/platform_capability_contracts.h"

struct SpawnParams {
    Side side;
    double x, y, z;
    double heading, pitch, roll;
    double vx, vy, vz;
};

class IUnitFactory {
  public:
    virtual ~IUnitFactory() = default;

    virtual const UnitDefinition *get_definition(const std::string &name) const = 0;

    // Read-only owner projection used by qualification and diagnostics. The
    // factory remains authoritative; this seam does not grant a spawn bypass.
    virtual runtime::platform_capabilities::ResolvedPlatformSpawnPlan
    resolve_platform_spawn_plan_for_type_name(std::string_view type_name) const {
        runtime::platform_capabilities::ResolvedPlatformSpawnPlan plan{};
        plan.source_request_kind = std::string(
            runtime::platform_capabilities::kPlatformSpawnRequestKindTypeNameProjection);
        plan.source_type_name = std::string(type_name);
        plan.type_name_projection_preserved = true;
        plan.admitted = false;
        plan.rejection_reason = "resolved_platform_spawn_plan_owner_projection_unavailable";
        plan.diagnostics_reason = plan.rejection_reason;
        return plan;
    }
    virtual flecs::entity spawn(flecs::world &ecs, const std::string &unit_name,
                                const SpawnParams &params) = 0;

    virtual bool load_definitions(const std::string & /*path*/, std::string *error) {
        if (error) *error = "UnitFactory does not support loading definitions.";
        return false;
    }
};
