#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_batch_setup(nb::module_ &m) {
    nb::class_<WorldEntityRef> world_entity_ref_class(m, "WorldEntityRef");
    world_entity_ref_class.def(nb::init<>());
#define EF_WORLD_ENTITY_REF_FIELD(type, name, default_value)                                       \
    world_entity_ref_class.def_rw(#name, &WorldEntityRef::name);
#include "runtime/contracts/detail/platform/world_entity_ref.inc"

    nb::class_<BatchWorldSetupRequest> batch_world_setup_request_class(m, "BatchWorldSetupRequest");
    batch_world_setup_request_class.def(nb::init<>());
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value)                              \
    batch_world_setup_request_class.def_rw(#name, &BatchWorldSetupRequest::name);
#include "runtime/facade/detail/batch/batch_world_setup_request.inc"

    // Field-order note: the header field order (schema-owned, ABI/aggregate-init
    // order) declares setup_surface before rejection_reason, but this
    // binding has long registered rejection_reason first. That pre-existing
    // divergence is preserved here (parity baseline) instead of being
    // macro-expanded from the same X-macro as the header block.
    nb::class_<TypedPlatformSpawnResult>(m, "TypedPlatformSpawnResult")
        .def(nb::init<>())
        .def_rw("request_index", &TypedPlatformSpawnResult::request_index)
        .def_rw("world_index", &TypedPlatformSpawnResult::world_index)
        .def_rw("entity_id", &TypedPlatformSpawnResult::entity_id)
        .def_rw("admitted", &TypedPlatformSpawnResult::admitted)
        .def_rw("materialized", &TypedPlatformSpawnResult::materialized)
        .def_rw("fail_closed", &TypedPlatformSpawnResult::fail_closed)
        .def_rw("request_id", &TypedPlatformSpawnResult::request_id)
        .def_rw("source_type_name", &TypedPlatformSpawnResult::source_type_name)
        .def_rw("plan_id", &TypedPlatformSpawnResult::plan_id)
        .def_rw("capability_bundle_id", &TypedPlatformSpawnResult::capability_bundle_id)
        .def_rw("rejection_reason", &TypedPlatformSpawnResult::rejection_reason)
        .def_rw("setup_surface", &TypedPlatformSpawnResult::setup_surface)
        .def_rw("errors", &TypedPlatformSpawnResult::errors)
        .def_rw("evidence_refs", &TypedPlatformSpawnResult::evidence_refs);

    nb::class_<BatchWorldSetupResult> batch_world_setup_result_class(m, "BatchWorldSetupResult");
    batch_world_setup_result_class.def(nb::init<>());
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value)                               \
    batch_world_setup_result_class.def_rw(#name, &BatchWorldSetupResult::name);
#include "runtime/facade/detail/batch/batch_world_setup_result.inc"
}
