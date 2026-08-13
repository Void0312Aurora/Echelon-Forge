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

void bind_episode_waypoint_approach(nb::module_ &m) {
    nb::class_<WaypointRewardInputs> wp_inputs_class(m, "WaypointRewardInputs");
    wp_inputs_class.def(nb::init<>());
#define EF_WAYPOINT_INPUT(type, name, default_value)                                               \
    wp_inputs_class.def_rw(#name, &WaypointRewardInputs::name);
#include "core/mission/runtime/detail/waypoint_reward_inputs.inc"

    nb::class_<WaypointRewardProducts> wp_products_class(m, "WaypointRewardProducts");
    wp_products_class.def(nb::init<>());
#define EF_WAYPOINT_PRODUCT(type, name, default_value)                                             \
    wp_products_class.def_ro(#name, &WaypointRewardProducts::name);
#include "core/mission/runtime/detail/waypoint_reward_products.inc"

    nb::class_<ApproachRewardInputs> approach_inputs_class(m, "ApproachRewardInputs");
    approach_inputs_class.def(nb::init<>());
#define EF_APPROACH_INPUT(type, name, default_value)                                               \
    approach_inputs_class.def_rw(#name, &ApproachRewardInputs::name);
#include "core/mission/runtime/detail/approach_reward_inputs.inc"

    nb::class_<ApproachRewardProducts> approach_products_class(m, "ApproachRewardProducts");
    approach_products_class.def(nb::init<>());
#define EF_APPROACH_PRODUCT(type, name, default_value)                                             \
    approach_products_class.def_ro(#name, &ApproachRewardProducts::name);
#include "core/mission/runtime/detail/approach_reward_products.inc"

    m.def("compute_waypoint_reward_terms", &compute_waypoint_reward_terms, nb::arg("inputs"));
    m.def("compute_approach_reward_terms", &compute_approach_reward_terms, nb::arg("inputs"));
}
