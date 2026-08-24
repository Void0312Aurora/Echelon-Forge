#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_platform(nb::module_ &m) {
    nb::class_<runtime::platform_capabilities::Capability> platform_capability_class(
        m, "PlatformCapability");
    platform_capability_class.def(nb::init<>());
#define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value)                                    \
    platform_capability_class.def_rw(#name, &runtime::platform_capabilities::Capability::name);
#include "runtime/contracts/detail/platform/platform_capability.inc"

    nb::class_<runtime::platform_capabilities::CapabilityBundle> capability_bundle_class(
        m, "CapabilityBundle");
    capability_bundle_class.def(nb::init<>());
#define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value)                                      \
    capability_bundle_class.def_rw(#name, &runtime::platform_capabilities::CapabilityBundle::name);
#include "runtime/contracts/detail/platform/capability_bundle.inc"

    nb::class_<runtime::platform_capabilities::ResolvedPlatformSpawnPlan>
        resolved_platform_spawn_plan_class(m, "ResolvedPlatformSpawnPlan");
    resolved_platform_spawn_plan_class.def(nb::init<>());
#define EF_RESOLVED_PLATFORM_SPAWN_PLAN_FIELD(type, name, default_value)                           \
    resolved_platform_spawn_plan_class.def_rw(                                                     \
        #name, &runtime::platform_capabilities::ResolvedPlatformSpawnPlan::name);
#include "runtime/contracts/detail/platform/resolved_platform_spawn_plan.inc"

    nb::class_<TypedPlatformSpawnRequest> typed_platform_spawn_request_class(
        m, "TypedPlatformSpawnRequest");
    typed_platform_spawn_request_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_REQUEST_FIELD(type, name, default_value)                           \
    typed_platform_spawn_request_class.def_rw(#name, &TypedPlatformSpawnRequest::name);
#include "runtime/contracts/detail/platform/typed_platform_spawn_request.inc"

    nb::class_<TypedPlatformSpawnValidationResult> typed_platform_spawn_validation_result_class(
        m, "TypedPlatformSpawnValidationResult");
    typed_platform_spawn_validation_result_class.def(nb::init<>());
#define EF_TYPED_PLATFORM_SPAWN_VALIDATION_RESULT_FIELD(type, name, default_value)                 \
    typed_platform_spawn_validation_result_class.def_rw(                                           \
        #name, &TypedPlatformSpawnValidationResult::name);
#include "runtime/contracts/detail/platform/typed_platform_spawn_validation_result.inc"

    nb::class_<BatchResetRequest> batch_reset_request_class(m, "BatchResetRequest");
    batch_reset_request_class.def(nb::init<>());
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value)                                    \
    batch_reset_request_class.def_rw(#name, &BatchResetRequest::name);
#include "runtime/facade/detail/batch/batch_reset_request.inc"
}
