#include "interfaces/python/bindings_core_detail.h"

#include "components/basic/common.h"
#include "components/domains/ground/combat/weapon_ground.h"
#include "components/systems/sensor.h"
#include "core/interfaces/observation.h"

void bind_core_enums(nb::module_ &m) {
    nb::enum_<Side>(m, "Side")
        .value("Blue", Side::Blue)
        .value("Red", Side::Red)
        .value("Neutral", Side::Neutral)
        .value("Unknown", Side::Unknown)
        .export_values();

    nb::class_<RWREvent>(m, "RWREvent")
        .def_ro("source_id", &RWREvent::source_id)
        .def_ro("bearing", &RWREvent::bearing)
        .def_ro("signal_strength", &RWREvent::signal_strength)
        .def_ro("is_lock", &RWREvent::is_lock)
        .def_ro("is_launch", &RWREvent::is_launch);

    nb::class_<ESMEvent>(m, "ESMEvent")
        .def_ro("source_id", &ESMEvent::source_id)
        .def_ro("bearing_deg", &ESMEvent::bearing_deg)
        .def_ro("signal_strength", &ESMEvent::signal_strength)
        .def_ro("received_power_dbm", &ESMEvent::received_power_dbm)
        .def_ro("has_rf_power", &ESMEvent::has_rf_power)
        .def_ro("sensitivity_margin_db", &ESMEvent::sensitivity_margin_db)
        .def_ro("observed_time_s", &ESMEvent::observed_time_s)
        .def_ro("age_s", &ESMEvent::age_s)
        .def_ro("confidence", &ESMEvent::confidence)
        .def_ro("classification_known", &ESMEvent::classification_known)
        .def_ro("is_jammer", &ESMEvent::is_jammer)
        .def_ro("is_lock", &ESMEvent::is_lock)
        .def_ro("is_guidance", &ESMEvent::is_guidance);

    // Bind UnitType Enum
    nb::enum_<UnitType>(m, "UnitType")
        .value("Aircraft", UnitType::Aircraft)
        .value("Ship", UnitType::Ship)
        .value("Submarine", UnitType::Submarine)
        .value("Ground", UnitType::Ground)
        .value("Missile", UnitType::Missile)
        .value("Facility", UnitType::Facility)
        .value("C2Node", UnitType::C2Node);

    nb::enum_<SensorType>(m, "SensorType")
        .value("Visual", SensorType::Visual)
        .value("Infrared", SensorType::Infrared)
        .value("Radar", SensorType::Radar)
        .value("RWR", SensorType::RWR)
        .value("MIDS", SensorType::MIDS)
        .value("ESM", SensorType::ESM)
        .value("Sonar", SensorType::Sonar);

    nb::enum_<GroundWeaponType>(m, "GroundWeaponType")
        .value("Unknown", GroundWeaponType::Unknown)
        .value("Rifle", GroundWeaponType::Rifle);
}
