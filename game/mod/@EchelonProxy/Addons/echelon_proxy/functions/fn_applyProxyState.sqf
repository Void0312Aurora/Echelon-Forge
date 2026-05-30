params [
    ["_payload", "", [""]]
];

if (_payload isEqualTo "") exitWith {false};

private _state = parseSimpleArray _payload;
if !(_state isEqualType []) exitWith {false};
if ((count _state) < 9) exitWith {false};

private _frameId = _state param [0, -1];
private _lastFrameId = missionNamespace getVariable ["EPX_lastAppliedFrame", -1];
if (_frameId <= _lastFrameId) exitWith {false};

private _posAsl = _state param [1, [0, 0, 100]];
private _velWorld = _state param [2, [0, 0, 0]];
private _dir = _state param [3, [1, 0, 0]];
private _up = _state param [4, [0, 0, 1]];

private _proxy = missionNamespace getVariable ["EPX_proxyVehicle", objNull];
if (isNull _proxy) then {
    _proxy = [_posAsl] call EPX_fnc_spawnProxyAircraft;
};

_proxy setPosASL _posAsl;
_proxy setVelocity _velWorld;
_proxy setVectorDirAndUp [_dir, _up];

missionNamespace setVariable ["EPX_lastAppliedFrame", _frameId];
true
