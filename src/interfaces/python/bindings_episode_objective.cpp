#include "interfaces/python/bindings_episode_detail.h"

#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/episode/episode_reward_breakdown.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/episode/execution_episode_state.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/execution_step_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "core/mission/runtime/objective_runtime.h"
#include "core/mission/runtime/reward_runtime.h"
#include "core/mission/runtime/termination_runtime.h"

void bind_episode_objective(nb::module_ &m) {
    nb::enum_<ConditionalObjectiveProperty>(m, "ConditionalObjectiveProperty")
        .value("Unknown", ConditionalObjectiveProperty::Unknown)
        .value("Altitude", ConditionalObjectiveProperty::Altitude)
        .value("AltitudeAGL", ConditionalObjectiveProperty::AltitudeAGL)
        .value("Speed", ConditionalObjectiveProperty::Speed)
        .value("GroundSpeed", ConditionalObjectiveProperty::GroundSpeed)
        .value("Gear", ConditionalObjectiveProperty::Gear)
        .value("HeadingErrorDeg", ConditionalObjectiveProperty::HeadingErrorDeg)
        .value("CommandCode", ConditionalObjectiveProperty::CommandCode)
        .value("GroundTrackErrorDeg", ConditionalObjectiveProperty::GroundTrackErrorDeg)
        .value("RunwayCrossAbsM", ConditionalObjectiveProperty::RunwayCrossAbsM)
        .value("RunwayFromThresholdM", ConditionalObjectiveProperty::RunwayFromThresholdM)
        .value("OnRunwayGeom", ConditionalObjectiveProperty::OnRunwayGeom)
        .value("OnRunway", ConditionalObjectiveProperty::OnRunway)
        .value("OnGround", ConditionalObjectiveProperty::OnGround)
        .value("SinkRateAbsMps", ConditionalObjectiveProperty::SinkRateAbsMps)
        .value("IlsLocalizerAbs", ConditionalObjectiveProperty::IlsLocalizerAbs)
        .value("IlsGlideslopeAbs", ConditionalObjectiveProperty::IlsGlideslopeAbs)
        .value("DmeM", ConditionalObjectiveProperty::DmeM)
        .value("Heading", ConditionalObjectiveProperty::Heading)
        .value("X", ConditionalObjectiveProperty::X)
        .value("Y", ConditionalObjectiveProperty::Y)
        .value("SelfActive", ConditionalObjectiveProperty::SelfActive)
        .value("TargetActive", ConditionalObjectiveProperty::TargetActive)
        .value("SelfHealth", ConditionalObjectiveProperty::SelfHealth)
        .value("TargetHealth", ConditionalObjectiveProperty::TargetHealth)
        .value("MissilesRemaining", ConditionalObjectiveProperty::MissilesRemaining)
        .value("TargetRangeM", ConditionalObjectiveProperty::TargetRangeM)
        .export_values();

    nb::enum_<ConditionalObjectiveOp>(m, "ConditionalObjectiveOp")
        .value("GreaterEqual", ConditionalObjectiveOp::GreaterEqual)
        .value("GreaterThan", ConditionalObjectiveOp::GreaterThan)
        .value("LessEqual", ConditionalObjectiveOp::LessEqual)
        .value("LessThan", ConditionalObjectiveOp::LessThan)
        .export_values();

    nb::enum_<ConditionalObjectiveTargetKind>(m, "ConditionalObjectiveTargetKind")
        .value("Literal", ConditionalObjectiveTargetKind::Literal)
        .value("CommandAltitude", ConditionalObjectiveTargetKind::CommandAltitude)
        .value("CommandSpeed", ConditionalObjectiveTargetKind::CommandSpeed)
        .value("CommandHeading", ConditionalObjectiveTargetKind::CommandHeading)
        .export_values();

    nb::class_<ConditionalObjectiveCondition>(m, "ConditionalObjectiveCondition")
        .def(nb::init<>())
        .def_rw("property_code", &ConditionalObjectiveCondition::property_code)
        .def_rw("op_code", &ConditionalObjectiveCondition::op_code)
        .def_rw("target_kind", &ConditionalObjectiveCondition::target_kind)
        .def_rw("target_value", &ConditionalObjectiveCondition::target_value)
        .def_rw("target_scale", &ConditionalObjectiveCondition::target_scale);

    nb::class_<ConditionalObjectiveSpec>(m, "ConditionalObjectiveSpec")
        .def(nb::init<>())
        .def_rw("conditions", &ConditionalObjectiveSpec::conditions)
        .def_rw("reward_bonus", &ConditionalObjectiveSpec::reward_bonus);

    nb::class_<ConditionalObjectiveInputs> obj_inputs_class(m, "ConditionalObjectiveInputs");
    obj_inputs_class.def(nb::init<>());
#define EF_OBJECTIVE_INPUT(type, name, default_value)                                              \
    obj_inputs_class.def_rw(#name, &ConditionalObjectiveInputs::name);
#include "core/mission/runtime/detail/objective_inputs.inc"

    nb::class_<ObjectiveShapingConfig> obj_shaping_class(m, "ObjectiveShapingConfig");
    obj_shaping_class.def(nb::init<>());
#define EF_OBJECTIVE_SHAPING(type, name, default_value)                                            \
    obj_shaping_class.def_rw(#name, &ObjectiveShapingConfig::name);
#include "core/mission/runtime/detail/objective_shaping.inc"

    nb::class_<ConditionalObjectiveProducts> obj_products_class(m, "ConditionalObjectiveProducts");
    obj_products_class.def(nb::init<>());
#define EF_OBJECTIVE_PRODUCT(type, name, default_value)                                            \
    obj_products_class.def_ro(#name, &ConditionalObjectiveProducts::name);
#include "core/mission/runtime/detail/objective_products.inc"

    m.def("evaluate_conditional_objective", &evaluate_conditional_objective, nb::arg("spec"),
          nb::arg("inputs"), nb::arg("shaping"));
}
