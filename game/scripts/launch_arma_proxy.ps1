param(
    [ValidateSet("StubAndArma", "StubOnly", "ArmaOnly")]
    [string]$Mode = "StubAndArma",

    [ValidateSet("Stub", "EchelonEnv")]
    [string]$BackendKind = "Stub",

    [string]$ArmaRoot = "F:\SteamLibrary\steamapps\common\Arma 3",
    [string]$ExtraMods = "",
    [string]$MissionFile = "",

    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8765,

    [double]$StartX = 1200.0,
    [double]$StartY = 3400.0,
    [double]$StartZ = 1500.0,
    [double]$SpeedMps = 220.0,
    [double]$TurnRateDegS = 0.0,
    [double]$ClimbRateMps = 0.0,

    [string]$Scenario = "scenarios/stable_flight/stable_flight.json",
    [string]$ActionMode = "full",
    [string]$MissionObsMode = "basic",

    [switch]$ReuseExistingBackend,
    [switch]$ShowScriptErrors,
    [switch]$DebugCallExtension
)

$ErrorActionPreference = "Stop"

function Test-EpxStubReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ListenHost,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $client = $null
    $stream = $null
    $writer = $null
    $reader = $null

    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $async = $client.ConnectAsync($ListenHost, $Port)
        if (-not $async.Wait(500)) {
            return $false
        }

        $stream = $client.GetStream()
        $stream.ReadTimeout = 500
        $stream.WriteTimeout = 500

        $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
        $writer = [System.IO.StreamWriter]::new($stream, $utf8NoBom, 1024, $true)
        $writer.NewLine = "`n"
        $writer.AutoFlush = $true
        $reader = [System.IO.StreamReader]::new($stream, $utf8NoBom, $false, 1024, $true)

        $writer.WriteLine("status")
        $reply = $reader.ReadLine()
        return ($reply -like "status`t*")
    } catch {
        return $false
    } finally {
        if ($reader) { $reader.Dispose() }
        if ($writer) { $writer.Dispose() }
        if ($stream) { $stream.Dispose() }
        if ($client) { $client.Dispose() }
    }
}

function Wait-EpxStubReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ListenHost,

        [Parameter(Mandatory = $true)]
        [int]$Port,

        [int]$TimeoutMs = 8000
    )

    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-EpxStubReady -ListenHost $ListenHost -Port $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

function Start-EpxBackendProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        [Parameter(Mandatory = $true)]
        [string]$BackendKind,

        [Parameter(Mandatory = $true)]
        [string]$ListenHost,

        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [double]$StartX,

        [Parameter(Mandatory = $true)]
        [double]$StartY,

        [Parameter(Mandatory = $true)]
        [double]$StartZ,

        [Parameter(Mandatory = $true)]
        [double]$SpeedMps,

        [Parameter(Mandatory = $true)]
        [double]$TurnRateDegS,

        [Parameter(Mandatory = $true)]
        [double]$ClimbRateMps,

        [Parameter(Mandatory = $true)]
        [string]$Scenario,

        [Parameter(Mandatory = $true)]
        [string]$ActionMode,

        [Parameter(Mandatory = $true)]
        [string]$MissionObsMode,

        [switch]$ReuseExistingBackend
    )

    if (Test-EpxStubReady -ListenHost $ListenHost -Port $Port) {
        if (-not $ReuseExistingBackend) {
            throw "A stub-like backend is already listening on ${ListenHost}:${Port}. Re-run with -ReuseExistingBackend to attach to it."
        }
        Write-Host "[EPX] Reusing existing backend at ${ListenHost}:${Port}"
        return $null
    }

    $PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw "Repository virtualenv Python not found: $PythonExe"
    }

    $BackendScript = switch ($BackendKind) {
        "Stub" {
            Join-Path $RepoRoot "tools\diagnostics\arma_proxy_backend_stub.py"
        }
        "EchelonEnv" {
            Join-Path $RepoRoot "tools\diagnostics\arma_proxy_backend_echelon_env.py"
        }
        default {
            throw "Unsupported backend kind: $BackendKind"
        }
    }
    if (-not (Test-Path -LiteralPath $BackendScript)) {
        throw "Backend script not found: $BackendScript"
    }

    $RuntimeDir = Join-Path $RepoRoot "game\runtime"
    $LogDir = Join-Path $RepoRoot "game\logs"
    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

    $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $BackendSlug = if ($BackendKind -eq "EchelonEnv") { "arma_proxy_echelon_env" } else { "arma_proxy_stub" }
    $StdoutLog = Join-Path $LogDir "$BackendSlug-$Stamp.out.log"
    $StderrLog = Join-Path $LogDir "$BackendSlug-$Stamp.err.log"
    $MetaPath = Join-Path $RuntimeDir "last_backend.json"

    $ArgList = @(
        "-u",
        $BackendScript,
        "--host", $ListenHost,
        "--port", "$Port"
    )
    if ($BackendKind -eq "Stub") {
        $ArgList += @(
            "--start-position", "$StartX", "$StartY", "$StartZ",
            "--speed-mps", "$SpeedMps",
            "--turn-rate-deg-s", "$TurnRateDegS",
            "--climb-rate-mps", "$ClimbRateMps"
        )
    } elseif ($BackendKind -eq "EchelonEnv") {
        $ArgList += @(
            "--scenario", $Scenario,
            "--action-mode", $ActionMode,
            "--mission-obs-mode", $MissionObsMode
        )
    }

    $process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList $ArgList `
        -WorkingDirectory $RepoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdoutLog `
        -RedirectStandardError $StderrLog `
        -PassThru

    $metadata = @{
        pid = $process.Id
        backend_kind = $BackendKind
        host = $ListenHost
        port = $Port
        stdout_log = $StdoutLog
        stderr_log = $StderrLog
        started_at = (Get-Date).ToString("s")
        scenario = $Scenario
    } | ConvertTo-Json
    Set-Content -LiteralPath $MetaPath -Value $metadata -Encoding ASCII

    if (-not (Wait-EpxStubReady -ListenHost $ListenHost -Port $Port -TimeoutMs 8000)) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
        throw "Backend stub failed to become ready on ${ListenHost}:${Port}. See logs: $StdoutLog and $StderrLog"
    }

    Write-Host "[EPX] Started backend $BackendKind PID $($process.Id) on ${ListenHost}:${Port}"
    Write-Host "[EPX] Backend logs:"
    Write-Host "  $StdoutLog"
    if (Test-Path -LiteralPath $StderrLog) {
        Write-Host "  $StderrLog"
    }
    return $process
}

$GameRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $GameRoot
$ProxyMod = Join-Path $GameRoot "mod\@EchelonProxy"
$ArmaExe = Join-Path $ArmaRoot "arma3_x64.exe"
$NeedsStub = $Mode -ne "ArmaOnly"
$NeedsArma = $Mode -ne "StubOnly"

if (-not (Test-Path -LiteralPath $ProxyMod)) {
    throw "Proxy mod directory not found: $ProxyMod"
}

if ($NeedsStub) {
    Start-EpxBackendProcess `
        -RepoRoot $RepoRoot `
        -BackendKind $BackendKind `
        -ListenHost $BackendHost `
        -Port $BackendPort `
        -StartX $StartX `
        -StartY $StartY `
        -StartZ $StartZ `
        -SpeedMps $SpeedMps `
        -TurnRateDegS $TurnRateDegS `
        -ClimbRateMps $ClimbRateMps `
        -Scenario $Scenario `
        -ActionMode $ActionMode `
        -MissionObsMode $MissionObsMode `
        -ReuseExistingBackend:$ReuseExistingBackend | Out-Null
}

if (-not $NeedsArma) {
    Write-Host "[EPX] StubOnly mode complete."
    exit 0
}

if (-not (Test-Path -LiteralPath $ArmaExe)) {
    throw "Arma 3 executable not found: $ArmaExe"
}

$BridgeDll = Join-Path $ProxyMod "echelon_bridge.dll"
if (-not (Test-Path -LiteralPath $BridgeDll)) {
    throw "Bridge DLL not found: $BridgeDll`nBuild it first with game/scripts/build_bridge.ps1"
}

$Mods = @($ProxyMod)
if (-not [string]::IsNullOrWhiteSpace($ExtraMods)) {
    $Mods += ($ExtraMods -split ";")
}

$ArgList = @(
    "-noSplash",
    "-skipIntro",
    "-filePatching",
    "-mod=" + ($Mods -join ";")
)

if ($ShowScriptErrors) {
    $ArgList += "-showScriptErrors"
}

if ($DebugCallExtension) {
    $ArgList += "-debugCallExtension"
}

if (-not [string]::IsNullOrWhiteSpace($MissionFile)) {
    $ResolvedMission = Resolve-Path -LiteralPath $MissionFile -ErrorAction Stop
    $ArgList += $ResolvedMission.Path
}

Write-Host "[EPX] Launch mode: $Mode"
Write-Host "[EPX] Launching Arma 3 with mods:"
$Mods | ForEach-Object { Write-Host "  $_" }
Write-Host "[EPX] Startup args:"
$ArgList | ForEach-Object { Write-Host "  $_" }

Start-Process -FilePath $ArmaExe -ArgumentList $ArgList
