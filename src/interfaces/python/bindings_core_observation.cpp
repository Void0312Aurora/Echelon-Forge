#include "interfaces/python/bindings_core_detail.h"

#include "core/interfaces/observation.h"
#include "runtime/contracts/engagement_contracts.h"

void bind_core_observation(nb::module_ &m) {
    nb::class_<AgentObservation>(m, "AgentObservation")
        .def_ro("sim_time", &AgentObservation::sim_time)
        .def_ro("id", &AgentObservation::id)
        .def_ro("x", &AgentObservation::x)
        .def_ro("y", &AgentObservation::y)
        .def_ro("z", &AgentObservation::z)
        .def_ro("vx", &AgentObservation::vx)
        .def_ro("vy", &AgentObservation::vy)
        .def_ro("vz", &AgentObservation::vz)
        .def_ro("heading", &AgentObservation::heading)
        .def_ro("pitch", &AgentObservation::pitch)
        .def_ro("roll", &AgentObservation::roll)
        .def_ro("speed", &AgentObservation::speed)
        .def_ro("health", &AgentObservation::health)
        .def_ro("contacts", &AgentObservation::contacts)
        .def_ro("rwr_warnings", &AgentObservation::rwr_warnings)
        .def_ro("missiles_remaining", &AgentObservation::missiles_remaining)
        .def_ro("can_fire", &AgentObservation::can_fire)
        .def_ro("gear_state", &AgentObservation::gear_state)
        .def_ro("throttle", &AgentObservation::throttle)
        .def_ro("total_reward", &AgentObservation::total_reward);

    nb::class_<RecentEngagementEvents> recent_engagement_events_class(m, "RecentEngagementEvents");
    recent_engagement_events_class.def(nb::init<>());
#define EF_RECENT_ENGAGEMENT_EVENTS_FIELD(type, name, default_value)                               \
    recent_engagement_events_class.def_rw(#name, &RecentEngagementEvents::name);
#include "runtime/contracts/detail/engagement/recent_engagement_events.inc"
}
