#include "interfaces/python/bindings_core_detail.h"

#include "components/systems/sensor.h"
#include "core/interfaces/observation.h"
#include "core/interfaces/unit_data.h"

void bind_core_unit_data(nb::module_ &m) {
    nb::class_<UnitData>(m, "UnitData")
        .def_ro("id", &UnitData::id)
        .def_ro("side", &UnitData::side)
        .def_ro("type", &UnitData::type)
        .def_ro("x", &UnitData::x)
        .def_ro("y", &UnitData::y)
        .def_ro("z", &UnitData::z)
        .def_ro("heading", &UnitData::heading);

    nb::class_<Detection>(m, "Detection")
        .def(nb::init<>())
        .def_rw("target_id", &Detection::target_id)
        .def_rw("range", &Detection::range)
        .def_rw("bearing", &Detection::bearing)
        .def_rw("elevation", &Detection::elevation)
        .def_rw("closing_speed", &Detection::closing_speed)
        .def_rw("signal_strength", &Detection::signal_strength)
        .def_rw("snr_db", &Detection::snr_db)
        .def_rw("detection_prob_used", &Detection::detection_prob_used)
        .def_rw("measured_vr", &Detection::measured_vr)
        .def_rw("sensor_type", &Detection::sensor_type)
        .def_rw("local_sensor_hit", &Detection::local_sensor_hit)
        .def_rw("timestamp", &Detection::timestamp);

    nb::class_<TrackData>(m, "TrackData")
        .def_ro("id", &TrackData::id)
        .def_ro("range", &TrackData::range)
        .def_ro("azimuth", &TrackData::azimuth)
        .def_ro("elevation", &TrackData::elevation)
        .def_ro("closing_speed", &TrackData::closing_speed)
        .def_ro("time_since_update", &TrackData::time_since_update)
        .def_ro("source", &TrackData::source)
        .def_ro("classification", &TrackData::classification)
        .def_ro("status", &TrackData::status)
        .def_ro("quality", &TrackData::quality)
        .def_ro("confidence", &TrackData::confidence)
        .def_ro("usability", &TrackData::usability)
        .def_ro("iff_known", &TrackData::iff_known)
        .def_ro("classification_confidence", &TrackData::classification_confidence);
}
