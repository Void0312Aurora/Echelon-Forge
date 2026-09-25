"""Ground-domain training contracts and explicitly bounded adapters.

The package is intentionally separate from the maintained WorldBatch air
action path.  It contains both a deterministic engineering proxy and a
single-soldier native probe/Gym adapter; the latter remains ``native_probe_only``
until a reviewed production Ground training owner is admitted.
"""

from .infantry_proxy import (
    GROUND_INFANTRY_ACTION_MODE,
    GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
    GroundFieldProxy,
    GroundInfantryAction,
    GroundInfantryProxyError,
    GroundInfantryState,
    GroundInfantryTransition,
    GroundBridgeRoutePlan,
    build_ground_infantry_command,
    normalize_ground_infantry_action,
)
from .command import (
    build_ground_infantry_maintained_assignment,
    build_ground_infantry_mission_command,
)
from .proxy_env import GroundInfantryProxyEnv
from .native_probe import (
    GroundInfantryNativeProbe,
    GroundInfantryNativeProbeError,
    NATIVE_GROUND_PROBE_CONTRACT_VERSION,
    NativeGroundFireResult,
    NativeGroundRouteValidation,
    NativeGroundInfantryTransition,
)
from .native_env import GroundInfantryNativeEnv

__all__ = [
    "GROUND_INFANTRY_ACTION_MODE",
    "GROUND_INFANTRY_PROXY_CONTRACT_VERSION",
    "GroundFieldProxy",
    "GroundInfantryAction",
    "GroundInfantryProxyError",
    "GroundInfantryState",
    "GroundInfantryTransition",
    "GroundBridgeRoutePlan",
    "GroundInfantryProxyEnv",
    "GroundInfantryNativeProbe",
    "GroundInfantryNativeProbeError",
    "NATIVE_GROUND_PROBE_CONTRACT_VERSION",
    "NativeGroundFireResult",
    "NativeGroundRouteValidation",
    "NativeGroundInfantryTransition",
    "GroundInfantryNativeEnv",
    "build_ground_infantry_command",
    "build_ground_infantry_maintained_assignment",
    "build_ground_infantry_mission_command",
    "normalize_ground_infantry_action",
]
