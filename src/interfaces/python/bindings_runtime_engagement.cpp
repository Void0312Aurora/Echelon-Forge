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

void bind_runtime_engagement(nb::module_ &m) {
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

    nb::class_<ComponentLoadEvent> component_load_event_class(m, "ComponentLoadEvent");
    component_load_event_class.def(nb::init<>());
#define EF_COMPONENT_LOAD_EVENT_FIELD(type, name, default_value)                                   \
    component_load_event_class.def_rw(#name, &ComponentLoadEvent::name);
#include "runtime/contracts/detail/damage/component_load_event.inc"

    nb::class_<ComponentDamageEvent> component_damage_event_class(m, "ComponentDamageEvent");
    component_damage_event_class.def(nb::init<>());
#define EF_COMPONENT_DAMAGE_EVENT_FIELD(type, name, default_value)                                 \
    component_damage_event_class.def_rw(#name, &ComponentDamageEvent::name);
#include "runtime/contracts/detail/damage/component_damage_event.inc"

    nb::class_<PlatformConsequenceEvent> platform_consequence_event_class(
        m, "PlatformConsequenceEvent");
    platform_consequence_event_class.def(nb::init<>());
#define EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(type, name, default_value)                             \
    platform_consequence_event_class.def_rw(#name, &PlatformConsequenceEvent::name);
#include "runtime/contracts/detail/damage/platform_consequence_event.inc"

    nb::class_<StructuralBreakupEvent> structural_breakup_event_class(m, "StructuralBreakupEvent");
    structural_breakup_event_class.def(nb::init<>());
#define EF_STRUCTURAL_BREAKUP_EVENT_FIELD(type, name, default_value)                               \
    structural_breakup_event_class.def_rw(#name, &StructuralBreakupEvent::name);
#include "runtime/contracts/detail/damage/structural_breakup_event.inc"

    nb::class_<LifecycleTransitionEvent> lifecycle_transition_event_class(
        m, "LifecycleTransitionEvent");
    lifecycle_transition_event_class.def(nb::init<>());
#define EF_LIFECYCLE_TRANSITION_EVENT_FIELD(type, name, default_value)                             \
    lifecycle_transition_event_class.def_rw(#name, &LifecycleTransitionEvent::name);
#include "runtime/contracts/detail/damage/lifecycle_transition_event.inc"

    nb::class_<TrainingProjectionEvent> training_projection_event_class(m,
                                                                        "TrainingProjectionEvent");
    training_projection_event_class.def(nb::init<>());
#define EF_TRAINING_PROJECTION_EVENT_FIELD(type, name, default_value)                              \
    training_projection_event_class.def_rw(#name, &TrainingProjectionEvent::name);
#include "runtime/contracts/detail/damage/training_projection_event.inc"

    nb::class_<TrackPacket> track_packet_class(m, "TrackPacket");
    track_packet_class.def(nb::init<>());
#define EF_TRACK_PACKET_FIELD(type, name, default_value)                                           \
    track_packet_class.def_rw(#name, &TrackPacket::name);
#include "runtime/contracts/detail/engagement/track_packet.inc"

    nb::class_<LaunchRequest> launch_request_class(m, "LaunchRequest");
    launch_request_class.def(nb::init<>());
#define EF_LAUNCH_REQUEST_FIELD(type, name, default_value)                                         \
    launch_request_class.def_rw(#name, &LaunchRequest::name);
#include "runtime/contracts/detail/engagement/launch_request.inc"

    nb::class_<LaunchEvent> launch_event_class(m, "LaunchEvent");
    launch_event_class.def(nb::init<>());
#define EF_LAUNCH_EVENT_FIELD(type, name, default_value)                                           \
    launch_event_class.def_rw(#name, &LaunchEvent::name);
#include "runtime/contracts/detail/engagement/launch_event.inc"

    nb::class_<MunitionLifecyclePacket> munition_lifecycle_packet_class(m,
                                                                        "MunitionLifecyclePacket");
    munition_lifecycle_packet_class.def(nb::init<>());
#define EF_MUNITION_LIFECYCLE_PACKET_FIELD(type, name, default_value)                              \
    munition_lifecycle_packet_class.def_rw(#name, &MunitionLifecyclePacket::name);
#include "runtime/contracts/detail/engagement/munition_lifecycle_packet.inc"

    nb::class_<ComponentMechanismLoadRow> component_mechanism_load_row_class(
        m, "ComponentMechanismLoadRow");
    component_mechanism_load_row_class.def(nb::init<>());
#define EF_COMPONENT_MECHANISM_LOAD_ROW_FIELD(type, name, default_value)                           \
    component_mechanism_load_row_class.def_rw(#name, &ComponentMechanismLoadRow::name);
#include "runtime/contracts/detail/damage/component_mechanism_load_row.inc"

    nb::class_<ComponentResponseRow> component_response_row_class(m, "ComponentResponseRow");
    component_response_row_class.def(nb::init<>());
#define EF_COMPONENT_RESPONSE_ROW_FIELD(type, name, default_value)                                 \
    component_response_row_class.def_rw(#name, &ComponentResponseRow::name);
#include "runtime/contracts/detail/damage/component_response_row.inc"

    // The def_rw list is owned by the X-macro field list; exposed property
    // names and their order stay identical to the EffectsEvent declaration.
    nb::class_<EffectsEvent>(m, "EffectsEvent").def(nb::init<>())
#define EF_EFFECTS_EVENT_FIELD(type, name, default_value) .def_rw(#name, &EffectsEvent::name)
#define EF_EFFECTS_EVENT_RESULT_FIELD(type, name, default_value) .def_rw(#name, &EffectsEvent::name)
#include "runtime/contracts/detail/damage/effects_event_fields.inc"
#undef EF_EFFECTS_EVENT_RESULT_FIELD
#undef EF_EFFECTS_EVENT_FIELD
        ;
}
