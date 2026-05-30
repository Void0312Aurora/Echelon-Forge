if (missionNamespace getVariable ["EPX_loopInstalled", false]) exitWith {};

missionNamespace setVariable ["EPX_loopInstalled", true];
missionNamespace setVariable ["EPX_extensionName", "echelon_bridge"];
missionNamespace setVariable ["EPX_backendHost", "127.0.0.1"];
missionNamespace setVariable ["EPX_backendPort", 8765];
missionNamespace setVariable ["EPX_sessionId", format ["arma_local_%1", floor diag_tickTime]];
missionNamespace setVariable ["EPX_proxyVehicleClass", "B_Plane_Fighter_01_F"];
missionNamespace setVariable ["EPX_sessionActive", false];
missionNamespace setVariable ["EPX_proxyVehicle", objNull];
missionNamespace setVariable ["EPX_lastTickTime", diag_tickTime];
missionNamespace setVariable ["EPX_lastAppliedFrame", -1];

addMissionEventHandler ["EachFrame", {
    [] call EPX_fnc_tick;
}];

[] call EPX_fnc_startSession;
