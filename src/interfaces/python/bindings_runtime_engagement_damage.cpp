#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_engagement_damage(nb::module_ &m) {
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
}
