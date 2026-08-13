#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_engagement_munition(nb::module_ &m) {
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
