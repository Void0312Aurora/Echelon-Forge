#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_engagement_track_launch(nb::module_ &m) {
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
}
