params [
    ["_functionName", "", [""]],
    ["_args", [], [[]]]
];

private _extensionName = missionNamespace getVariable ["EPX_extensionName", "echelon_bridge"];
private _raw = _extensionName callExtension [_functionName, _args];

if (_raw isEqualType []) exitWith {
    _raw
};

[_raw, 0, 0]
