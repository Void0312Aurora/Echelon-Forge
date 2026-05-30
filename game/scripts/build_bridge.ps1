param(
    [string]$Configuration = "RelWithDebInfo"
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$BridgeDir = Join-Path $RootDir "bridge"
$BuildDir = Join-Path $BridgeDir "build"
$VcVarsCandidates = @(
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
)

if (-not (Test-Path $BridgeDir)) {
    throw "Bridge directory not found: $BridgeDir"
}

$VcVars = $VcVarsCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $VcVars) {
    throw "Unable to locate vcvars64.bat. Install Visual Studio C++ build tools first."
}

$ConfigureCmd = "cmake -S `"$BridgeDir`" -B `"$BuildDir`" -G Ninja -DCMAKE_BUILD_TYPE=$Configuration"
$BuildCmd = "cmake --build `"$BuildDir`" --config $Configuration"
$CmdChain = "call `"$VcVars`" >nul 2>&1 && $ConfigureCmd && $BuildCmd"

Write-Host "[EPX] Using compiler environment: $VcVars"
cmd /c $CmdChain
if ($LASTEXITCODE -ne 0) {
    throw "Bridge build failed with exit code $LASTEXITCODE"
}

Write-Host "[EPX] Done. Expected output:"
Write-Host "  $(Join-Path $RootDir 'mod\@EchelonProxy\echelon_bridge.dll')"
