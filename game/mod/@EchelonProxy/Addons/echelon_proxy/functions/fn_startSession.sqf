private _host = missionNamespace getVariable ["EPX_backendHost", "127.0.0.1"];
private _port = missionNamespace getVariable ["EPX_backendPort", 8765];
private _sessionId = missionNamespace getVariable ["EPX_sessionId", "arma_local"];
private _proxyClass = missionNamespace getVariable ["EPX_proxyVehicleClass", "B_Plane_Fighter_01_F"];

private _cfg = ["configure_backend", [_host, str _port, _sessionId]] call EPX_fnc_extensionCall;
if ((_cfg param [1, 1]) != 0) exitWith {
    diag_log format ["[EPX] configure_backend failed: %1", _cfg];
};

private _start = ["begin_session", [_sessionId, worldName, _proxyClass]] call EPX_fnc_extensionCall;
if ((_start param [1, 1]) != 0) exitWith {
    diag_log format ["[EPX] begin_session failed: %1", _start];
};

missionNamespace setVariable ["EPX_sessionActive", true];
missionNamespace setVariable ["EPX_lastTickTime", diag_tickTime];
diag_log format ["[EPX] session started: %1", _sessionId];
