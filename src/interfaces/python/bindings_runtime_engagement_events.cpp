#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_engagement_events(nb::module_ &m) {
    nb::class_<EngagementEntityRef> engagement_entity_ref_class(m, "EngagementEntityRef");
    engagement_entity_ref_class.def(nb::init<>());
#define EF_ENGAGEMENT_ENTITY_REF_FIELD(type, name, default_value)                                  \
    engagement_entity_ref_class.def_rw(#name, &EngagementEntityRef::name);
#include "runtime/contracts/detail/engagement/engagement_entity_ref.inc"

    nb::class_<LethalityChainHeader> lethality_chain_header_class(m, "LethalityChainHeader");
    lethality_chain_header_class.def(nb::init<>());
#define EF_LETHALITY_CHAIN_HEADER_FIELD(type, name, default_value)                                 \
    lethality_chain_header_class.def_rw(#name, &LethalityChainHeader::name);
#include "runtime/contracts/detail/engagement/lethality_chain_header.inc"

    nb::class_<NearestApproachEvent> nearest_approach_event_class(m, "NearestApproachEvent");
    nearest_approach_event_class.def(nb::init<>());
#define EF_NEAREST_APPROACH_EVENT_FIELD(type, name, default_value)                                 \
    nearest_approach_event_class.def_rw(#name, &NearestApproachEvent::name);
#include "runtime/contracts/detail/engagement/nearest_approach_event.inc"

    nb::class_<FuzeEvaluationEvent> fuze_evaluation_event_class(m, "FuzeEvaluationEvent");
    fuze_evaluation_event_class.def(nb::init<>());
#define EF_FUZE_EVALUATION_EVENT_FIELD(type, name, default_value)                                  \
    fuze_evaluation_event_class.def_rw(#name, &FuzeEvaluationEvent::name);
#include "runtime/contracts/detail/engagement/fuze_evaluation_event.inc"

    nb::class_<WarheadMechanismEvent> warhead_mechanism_event_class(m, "WarheadMechanismEvent");
    warhead_mechanism_event_class.def(nb::init<>());
#define EF_WARHEAD_MECHANISM_EVENT_FIELD(type, name, default_value)                                \
    warhead_mechanism_event_class.def_rw(#name, &WarheadMechanismEvent::name);
#include "runtime/contracts/detail/engagement/warhead_mechanism_event.inc"

    nb::class_<SpatialCoverageEvent> spatial_coverage_event_class(m, "SpatialCoverageEvent");
    spatial_coverage_event_class.def(nb::init<>());
#define EF_SPATIAL_COVERAGE_EVENT_FIELD(type, name, default_value)                                 \
    spatial_coverage_event_class.def_rw(#name, &SpatialCoverageEvent::name);
#include "runtime/contracts/detail/engagement/spatial_coverage_event.inc"
}
