"""Ground-domain training contracts and explicitly bounded engineering proxies.

The package is intentionally separate from the maintained WorldBatch air
action path.  Nothing in this package claims to be a native Ground runtime
system; the proxy module is a deterministic scaffold until a reviewed Ground
movement/terrain owner is admitted to the C++ composition.
"""

from .infantry_proxy import (
    GROUND_INFANTRY_ACTION_MODE,
    GROUND_INFANTRY_PROXY_CONTRACT_VERSION,
    GroundFieldProxy,
    GroundInfantryAction,
    GroundInfantryProxyError,
    GroundInfantryState,
    GroundInfantryTransition,
    build_ground_infantry_command,
    normalize_ground_infantry_action,
)

__all__ = [
    "GROUND_INFANTRY_ACTION_MODE",
    "GROUND_INFANTRY_PROXY_CONTRACT_VERSION",
    "GroundFieldProxy",
    "GroundInfantryAction",
    "GroundInfantryProxyError",
    "GroundInfantryState",
    "GroundInfantryTransition",
    "build_ground_infantry_command",
    "normalize_ground_infantry_action",
]
