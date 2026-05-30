missionNamespace setVariable ["EPX_sessionActive", false];

private _sessionId = missionNamespace getVariable ["EPX_sessionId", "arma_local"];
private _stop = ["shutdown", [_sessionId]] call EPX_fnc_extensionCall;
diag_log format ["[EPX] shutdown reply: %1", _stop];

private _proxy = missionNamespace getVariable ["EPX_proxyVehicle", objNull];
if (!isNull _proxy) then {
    deleteVehicle _proxy;
    missionNamespace setVariable ["EPX_proxyVehicle", objNull];
};
