params [
    ["_initialPosAsl", [0, 0, 100], [[]]]
];

private _proxyClass = missionNamespace getVariable ["EPX_proxyVehicleClass", "B_Plane_Fighter_01_F"];
private _proxy = createVehicleLocal [_proxyClass, [0, 0, 0], [], 0, "CAN_COLLIDE"];

_proxy allowDamage false;
_proxy enableSimulationGlobal false;
_proxy setPosASL _initialPosAsl;
_proxy setVectorDirAndUp [[1, 0, 0], [0, 0, 1]];
_proxy setVelocity [0, 0, 0];

missionNamespace setVariable ["EPX_proxyVehicle", _proxy];
_proxy
