private _now = diag_tickTime;
private _last = missionNamespace getVariable ["EPX_lastTickTime", _now];
private _deltaS = (_now - _last) max 0;
missionNamespace setVariable ["EPX_lastTickTime", _now];

private _proxy = missionNamespace getVariable ["EPX_proxyVehicle", objNull];
private _posAsl = if (isNull _proxy) then {[0, 0, 0]} else {getPosASL _proxy};
private _velWorld = if (isNull _proxy) then {[0, 0, 0]} else {velocity _proxy};
private _dir = if (isNull _proxy) then {[1, 0, 0]} else {vectorDir _proxy};
private _up = if (isNull _proxy) then {[0, 0, 1]} else {vectorUp _proxy};
private _terrainAsl = getTerrainHeightASL [_posAsl select 0, _posAsl select 1];

str [
    1,
    worldName,
    _now,
    _deltaS,
    _terrainAsl,
    _posAsl,
    _velWorld,
    _dir,
    _up
]
