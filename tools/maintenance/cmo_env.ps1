$ErrorActionPreference = "Stop"

$ScriptArgs = @($args)
if ($ScriptArgs.Count -gt 0) {
    $Command = [string]$ScriptArgs[0]
} else {
    $Command = "summary"
}

if ($ScriptArgs.Count -gt 1) {
    $RemainingArgs = @($ScriptArgs[1..($ScriptArgs.Count - 1)])
} else {
    $RemainingArgs = @()
}

function Write-CmoError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    [Console]::Error.WriteLine($Message)
}

function Get-CmoRepoRoot {
    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $scriptDir "..\..")).Path
}

function Resolve-CmoCandidatePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir,

        [Parameter(Mandatory = $true)]
        [string]$Candidate
    )

    if ([System.IO.Path]::IsPathRooted($Candidate)) {
        return $Candidate
    }
    return (Join-Path $RootDir $Candidate)
}

function Get-CmoBuildCandidates {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    $candidates = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($env:CMO_BUILD_DIR)) {
        $candidates.Add($env:CMO_BUILD_DIR)
    }

    foreach ($name in @("build-local-win", "build-workshop", "build-gpu", "build", "build-facade-local")) {
        $candidates.Add($name)
    }

    $resolved = New-Object System.Collections.Generic.List[string]
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        $resolvedPath = Resolve-CmoCandidatePath -RootDir $RootDir -Candidate $candidate
        if (-not $resolved.Contains($resolvedPath)) {
            $resolved.Add($resolvedPath)
        }
    }
    return $resolved
}

function Test-CmoEfPyArtifact {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BuildDir
    )

    if (-not (Test-Path -LiteralPath $BuildDir -PathType Container)) {
        return $false
    }

    $searchDirs = @($BuildDir)
    foreach ($configName in @("Release", "RelWithDebInfo", "Debug")) {
        $configDir = Join-Path $BuildDir $configName
        if (Test-Path -LiteralPath $configDir -PathType Container) {
            $searchDirs += $configDir
        }
    }

    $patterns = @("ef_py*.pyd", "ef_py*.so", "ef_py")
    foreach ($dir in $searchDirs) {
        foreach ($pattern in $patterns) {
            $match = Get-ChildItem -LiteralPath $dir -Filter $pattern -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($null -ne $match) {
                return $true
            }
        }
    }
    return $false
}

function Find-CmoBuildDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    foreach ($candidate in (Get-CmoBuildCandidates -RootDir $RootDir)) {
        if ((Test-Path -LiteralPath $candidate -PathType Container) -and (Test-CmoEfPyArtifact -BuildDir $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Find-CmoEfPyImportDir {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BuildDir
    )

    $searchDirs = @($BuildDir)
    foreach ($configName in @("Release", "RelWithDebInfo", "Debug")) {
        $configDir = Join-Path $BuildDir $configName
        if (Test-Path -LiteralPath $configDir -PathType Container) {
            $searchDirs += $configDir
        }
    }

    $patterns = @("ef_py*.pyd", "ef_py*.so", "ef_py")
    foreach ($dir in $searchDirs) {
        foreach ($pattern in $patterns) {
            $match = Get-ChildItem -LiteralPath $dir -Filter $pattern -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($null -ne $match) {
                return (Resolve-Path -LiteralPath $dir).Path
            }
        }
    }

    return $BuildDir
}

function Find-CmoBuildCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    foreach ($candidate in (Get-CmoBuildCandidates -RootDir $RootDir)) {
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Get-CmoVenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    # Allow a shared interpreter to be supplied explicitly, mirroring how
    # CMO_BUILD_DIR lets several worktrees share one build snapshot.  Worktrees
    # created for a single task often have no .venv of their own, and
    # reconstructing one per worktree is slow and easy to get subtly wrong.
    #
    # Note CMO_PYTHON is also *exported* by Initialize-CmoEnv, so a child
    # process that invokes this script for a different repository now inherits
    # the parent's interpreter choice instead of resolving that repo's .venv;
    # clear CMO_PYTHON/CMO_VENV first for nested cross-repo invocations.
    if (-not [string]::IsNullOrWhiteSpace($env:CMO_PYTHON)) {
        return $env:CMO_PYTHON
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CMO_VENV)) {
        return (Join-Path $env:CMO_VENV "Scripts\python.exe")
    }

    return (Join-Path $RootDir ".venv\Scripts\python.exe")
}

function Join-CmoPythonPath {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Entries
    )

    $existingParts = @()
    if (-not [string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
        $existingParts = $env:PYTHONPATH -split [regex]::Escape([System.IO.Path]::PathSeparator)
    }

    $allParts = New-Object System.Collections.Generic.List[string]
    foreach ($entry in ($Entries + $existingParts)) {
        if ([string]::IsNullOrWhiteSpace($entry)) {
            continue
        }
        if (-not $allParts.Contains($entry)) {
            $allParts.Add($entry)
        }
    }

    return ($allParts -join [System.IO.Path]::PathSeparator)
}

function Join-CmoPath {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Entries
    )

    $existingParts = @()
    if (-not [string]::IsNullOrWhiteSpace($env:PATH)) {
        $existingParts = $env:PATH -split [regex]::Escape([System.IO.Path]::PathSeparator)
    }

    $allParts = New-Object System.Collections.Generic.List[string]
    foreach ($entry in ($Entries + $existingParts)) {
        if ([string]::IsNullOrWhiteSpace($entry)) {
            continue
        }
        if (-not $allParts.Contains($entry)) {
            $allParts.Add($entry)
        }
    }

    return ($allParts -join [System.IO.Path]::PathSeparator)
}

function Get-CmoRuntimePathEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BuildDir
    )

    $entries = New-Object System.Collections.Generic.List[string]
    foreach ($candidate in @(
        $BuildDir,
        (Join-Path $BuildDir "_deps\flecs-build"),
        (Join-Path $BuildDir "Release"),
        (Join-Path $BuildDir "RelWithDebInfo"),
        (Join-Path $BuildDir "Debug")
    )) {
        if ((Test-Path -LiteralPath $candidate -PathType Container) -and (-not $entries.Contains($candidate))) {
            $entries.Add((Resolve-Path -LiteralPath $candidate).Path)
        }
    }

    $compiler = Get-Command "g++.exe" -ErrorAction SilentlyContinue
    if ($null -ne $compiler) {
        $compilerDir = Split-Path -Parent $compiler.Source
        if (-not $entries.Contains($compilerDir)) {
            $entries.Add($compilerDir)
        }
    }

    return $entries
}

function Set-CmoWindowsDllSiteCustomize {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir,

        [Parameter(Mandatory = $true)]
        [string[]]$RuntimePathEntries
    )

    $siteDir = Join-Path $RootDir ".codex\cmo_env"
    if (-not (Test-Path -LiteralPath $siteDir -PathType Container)) {
        New-Item -ItemType Directory -Path $siteDir -Force | Out-Null
    }

    $escapedEntries = @()
    foreach ($entry in $RuntimePathEntries) {
        $escapedEntries += $entry.Replace("\", "\\").Replace("'", "\'")
    }

    $pathsLiteral = "'" + ($escapedEntries -join "', '") + "'"
    $sitecustomize = @"
import os

for _cmo_dll_dir in [$pathsLiteral]:
    if os.path.isdir(_cmo_dll_dir):
        try:
            os.add_dll_directory(_cmo_dll_dir)
        except (AttributeError, OSError):
            pass
"@

    Set-Content -LiteralPath (Join-Path $siteDir "sitecustomize.py") -Value $sitecustomize -Encoding ASCII
    return $siteDir
}

function Initialize-CmoEnv {
    $rootDir = Get-CmoRepoRoot
    $venvPython = Get-CmoVenvPython -RootDir $rootDir

    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        Write-CmoError "[cmo_env] missing repository virtualenv: $venvPython`n[cmo_env] create it with: py -3.11 -m venv .venv`n[cmo_env] or point at an existing one: `$env:CMO_VENV = 'D:\path\to\repo\.venv'"
        exit 2
    }

    $env:CMO_REPO_ROOT = $rootDir
    $env:CMO_PYTHON = $venvPython

    $buildDir = Find-CmoBuildDir -RootDir $rootDir
    if ($null -ne $buildDir) {
        $importDir = Find-CmoEfPyImportDir -BuildDir $buildDir
        $runtimePathEntries = Get-CmoRuntimePathEntries -BuildDir $buildDir
        $dllSiteDir = Set-CmoWindowsDllSiteCustomize -RootDir $rootDir -RuntimePathEntries $runtimePathEntries
        $env:CMO_BUILD_DIR = $buildDir
        $env:PYTHONPATH = Join-CmoPythonPath -Entries @($dllSiteDir, $importDir, $buildDir, $rootDir)
        $env:PATH = Join-CmoPath -Entries $runtimePathEntries
    } else {
        $env:PYTHONPATH = Join-CmoPythonPath -Entries @($rootDir)
    }
}

function Invoke-CmoPython {
    param(
        [string[]]$PythonArgs
    )

    Initialize-CmoEnv
    & $env:CMO_PYTHON @PythonArgs
    exit $LASTEXITCODE
}

function Show-CmoEnvSummary {
    Initialize-CmoEnv
    Write-Output "CMO_REPO_ROOT=$env:CMO_REPO_ROOT"
    Write-Output "CMO_PYTHON=$env:CMO_PYTHON"
    Write-Output "CMO_BUILD_DIR=$env:CMO_BUILD_DIR"
    Write-Output "PYTHONPATH=$env:PYTHONPATH"
}

function Test-CmoEnv {
    $rootDir = Get-CmoRepoRoot
    $venvPython = Get-CmoVenvPython -RootDir $rootDir

    if (-not (Test-Path -LiteralPath $rootDir -PathType Container)) {
        Write-CmoError "[cmo_env] repository root is not accessible: $rootDir"
        exit 1
    }

    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        Write-CmoError "[cmo_env] missing repository virtualenv: $venvPython`n[cmo_env] create it with: py -3.11 -m venv .venv`n[cmo_env] or point at an existing one: `$env:CMO_VENV = 'D:\path\to\repo\.venv'"
        exit 2
    }

    $buildDir = Find-CmoBuildDir -RootDir $rootDir
    if ($null -ne $buildDir) {
        Write-Output "[cmo_env] validation ok"
        Write-Output "CMO_REPO_ROOT=$rootDir"
        Write-Output "CMO_PYTHON=$venvPython"
        Write-Output "CMO_BUILD_DIR=$buildDir"
        Write-Output "CMO_RUNTIME_PATHS=$((Get-CmoRuntimePathEntries -BuildDir $buildDir) -join [System.IO.Path]::PathSeparator)"
        exit 0
    }

    $buildCandidate = Find-CmoBuildCandidate -RootDir $rootDir
    if ($null -eq $buildCandidate) {
        $searched = (Get-CmoBuildCandidates -RootDir $rootDir) -join ", "
        Write-CmoError "[cmo_env] missing build directory`n[cmo_env] searched: $searched`n[cmo_env] configure and build the project before running maintained workflows"
        exit 3
    }

    if (-not (Test-CmoEfPyArtifact -BuildDir $buildCandidate)) {
        Write-CmoError "[cmo_env] build directory exists but ef_py artifact is missing: $buildCandidate`n[cmo_env] expected one of: ef_py*.pyd, ef_py*.so, or ef_py"
        exit 4
    }

    Write-CmoError "[cmo_env] validation failed for an unknown reason"
    exit 5
}

function Test-CmoRlEnv {
    Initialize-CmoEnv
    $script = @'
import importlib
import sys

required = ("ef_py", "gymnasium", "stable_baselines3", "torch")
failed = False

for name in required:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        failed = True
        print(f"[cmo_env] import failed: {name}: {exc}", file=sys.stderr)
        continue
    version = getattr(module, "__version__", None)
    location = getattr(module, "__file__", None)
    detail = []
    if version:
        detail.append(f"version={version}")
    if location:
        detail.append(f"file={location}")
    suffix = f" ({', '.join(detail)})" if detail else ""
    print(f"[cmo_env] import ok: {name}{suffix}")

if failed:
    print(
        "[cmo_env] RL validation failed; install the `.[rl]` extra or the "
        "equivalent direct dependencies, and rebuild ef_py if that import failed.",
        file=sys.stderr,
    )
    sys.exit(6)

print("[cmo_env] RL validation ok")
'@

    & $env:CMO_PYTHON -c $script
    exit $LASTEXITCODE
}

try {
    switch ($Command) {
        "validate" {
            Test-CmoEnv
        }
        "validate-rl" {
            Test-CmoRlEnv
        }
        "summary" {
            Show-CmoEnvSummary
        }
        "python" {
            Invoke-CmoPython -PythonArgs $RemainingArgs
        }
        default {
            Invoke-CmoPython -PythonArgs (@($Command) + $RemainingArgs)
        }
    }
} catch {
    Write-CmoError $_.Exception.Message
    exit 1
}
