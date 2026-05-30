if !(missionNamespace getVariable ["EPX_sessionActive", false]) exitWith {};

private _hostFrame = [] call EPX_fnc_buildHostState;
private _submit = ["submit_host_frame", [_hostFrame]] call EPX_fnc_extensionCall;
private _submitCode = _submit param [1, 1];

if (_submitCode != 0) then {
    diag_log format ["[EPX] submit_host_frame failed: %1", _submit];
};

private _fetch = ["fetch_proxy_state", []] call EPX_fnc_extensionCall;
private _proxyState = _fetch param [0, ""];
private _fetchCode = _fetch param [1, 1];

if (_fetchCode != 0) exitWith {
    diag_log format ["[EPX] fetch_proxy_state failed: %1", _fetch];
};

[_proxyState] call EPX_fnc_applyProxyState;
