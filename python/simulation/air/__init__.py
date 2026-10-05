"""Compiled Air simulation adapters for the neutral scripted line."""

from .tasking import (
    CompiledAirC2TaskOrderProjection,
    apply_task_order_overrides,
    make_scripted_c2_task_manager,
)
from .observation import (
    AIR_SCRIPTED_MAX_CONTACTS,
    AIR_SCRIPTED_MAX_RWR,
    AIR_SCRIPTED_MISSION_MODE,
    build_air_contact_matrix,
    build_air_instrument_vector,
    build_air_mission_vector,
    build_air_rwr_matrix,
    build_air_scripted_observation,
)
from .director import AirDirectorDecision, AirDirectorInput, AirScriptedDirector
from .action import (
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AIR_FULL_ACTION_DIM,
    AIR_TAKEOFF2_ACTION_DIM,
    AIR_TAKEOFF4_ACTION_DIM,
    build_pilot_action,
    half_to_unit,
)
from .demo import AirFacadeDemoTrace, build_demo_setup, run_facade_scripted_demo
from .engagement import (
    AirEngagementDecision,
    AirEngagementFacts,
    AirScriptedEngagementController,
)
from .runtime import AirEngagementRuntimeInput, AirScriptedEngagementRuntimeModel
from .scenario_runtime import AirFacadeScenarioRun, AirFacadeScenarioRuntime, AirFacadeStepResult
from .tasking_runtime import AirScriptedTaskingRuntime
from .ew import AirEWDecision, AirScriptedEWController
from .coordination import AirScriptedRosterCoordinator, AirTargetAssignment
from .terminal import AirCombatTerminalEvaluator, AirCombatTerminalState

__all__ = [
    "AIR_SCRIPTED_MAX_CONTACTS",
    "AIR_SCRIPTED_MAX_RWR",
    "AIR_SCRIPTED_MISSION_MODE",
    "AirDirectorDecision",
    "AirDirectorInput",
    "AirScriptedDirector",
    "AIR_FULL_ACTION_DIM",
    "AIR_EW_HYBRID_ACTION_DIM",
    "AIR_EW_HYBRID_V2_ACTION_DIM",
    "AIR_TAKEOFF2_ACTION_DIM",
    "AIR_TAKEOFF4_ACTION_DIM",
    "CompiledAirC2TaskOrderProjection",
    "apply_task_order_overrides",
    "build_air_contact_matrix",
    "build_air_instrument_vector",
    "build_air_mission_vector",
    "build_air_rwr_matrix",
    "build_air_scripted_observation",
    "build_pilot_action",
    "half_to_unit",
    "AirFacadeDemoTrace",
    "build_demo_setup",
    "make_scripted_c2_task_manager",
    "run_facade_scripted_demo",
    "AirEngagementDecision",
    "AirEngagementFacts",
    "AirScriptedEngagementController",
    "AirEngagementRuntimeInput",
    "AirScriptedEngagementRuntimeModel",
    "AirFacadeScenarioRun",
    "AirFacadeScenarioRuntime",
    "AirFacadeStepResult",
    "AirScriptedTaskingRuntime",
    "AirEWDecision",
    "AirScriptedEWController",
    "AirScriptedRosterCoordinator",
    "AirTargetAssignment",
    "AirCombatTerminalEvaluator",
    "AirCombatTerminalState",
]
