param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,

    [Parameter(Mandatory = $true)]
    [string]$EnvFile,

    [Parameter(Mandatory = $true)]
    [int]$Port,

    [Parameter(Mandatory = $true)]
    [string]$LogLevel,

    [Parameter(Mandatory = $false)]
    [string]$AccessLogEnabled = "false",

    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Read-EnvFile {
    param([string]$Path)

    $result = @{}
    if (-not (Test-Path $Path)) {
        return $result
    }

    foreach ($raw in Get-Content -Path $Path -Encoding UTF8) {
        $line = $raw.Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.StartsWith("#")) { continue }

        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }

        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()

        if ($value.Length -ge 2) {
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }

        $result[$key] = $value
    }

    return $result
}

function Resolve-PythonExe {
    param(
        [string]$RepoRoot,
        [string]$Provided
    )

    if ($Provided -and (Test-Path $Provided)) {
        return (Resolve-Path $Provided).Path
    }

    $candidates = @(
        (Join-Path $RepoRoot ".venv-win\\Scripts\\python.exe"),
        (Join-Path $RepoRoot ".venv\\Scripts\\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($version in @("-3.12", "-3.11", "-3.10")) {
            $detected = & py $version -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $detected) {
                return $detected.Trim()
            }
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    throw "Unable to locate Windows Python interpreter. Set MT5_WINDOWS_PYTHON in .env."
}

function Test-BridgeDependencies {
    param([string]$PythonPath)

    $code = "import importlib.util,sys;mods=['uvicorn','fastapi','MetaTrader5'];missing=[m for m in mods if importlib.util.find_spec(m) is None];print(','.join(missing));sys.exit(0 if not missing else 1)"
    $output = & $PythonPath -c $code
    return @{
        Ok = ($LASTEXITCODE -eq 0)
        Missing = ($output | Out-String).Trim()
    }
}

function Ensure-WindowsVenv {
    param(
        [string]$RepoRoot,
        [string]$BootstrapPython
    )

    $venvRoot = Join-Path $RepoRoot ".venv-win"
    $venvPython = Join-Path $venvRoot "Scripts\\python.exe"
    $requirements = Join-Path $RepoRoot "requirements.txt"

    if (-not (Test-Path $venvPython)) {
        Write-Output "[windows-launcher] creating Windows venv at $venvRoot"
        & $BootstrapPython -m venv $venvRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create Windows venv at $venvRoot"
        }
    }

    Write-Output "[windows-launcher] installing/updating requirements in .venv-win"
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip in $venvPython"
    }

    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements from $requirements"
    }

    return $venvPython
}

if (-not (Test-Path $RepoRoot)) {
    throw "RepoRoot not found: $RepoRoot"
}

$envMap = Read-EnvFile -Path $EnvFile
foreach ($entry in $envMap.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, "Process")
}

$env:MT5_BRIDGE_PORT = "$Port"
$env:LOG_LEVEL = $LogLevel.ToLowerInvariant()

if (-not $env:MT5_BRIDGE_API_KEY) {
    throw "MT5_BRIDGE_API_KEY is required."
}

$python = Resolve-PythonExe -RepoRoot $RepoRoot -Provided $PythonExe
$autoSetup = $true
if ($env:LAUNCHER_AUTO_SETUP_WINDOWS_VENV) {
    $autoSetup = ($env:LAUNCHER_AUTO_SETUP_WINDOWS_VENV.ToLowerInvariant() -eq "true")
}

$depState = Test-BridgeDependencies -PythonPath $python
if (-not $depState.Ok) {
    if (-not $autoSetup) {
        throw "Python at $python is missing required modules: $($depState.Missing). Enable LAUNCHER_AUTO_SETUP_WINDOWS_VENV=true or set MT5_WINDOWS_PYTHON."
    }

    Write-Output "[windows-launcher] missing modules in selected python: $($depState.Missing)"
    $python = Ensure-WindowsVenv -RepoRoot $RepoRoot -BootstrapPython $python
    $depState = Test-BridgeDependencies -PythonPath $python
    if (-not $depState.Ok) {
        throw "Windows venv bootstrap completed but required modules are still missing: $($depState.Missing). Use Python 3.10-3.12 and rerun."
    }
}

Set-Location $RepoRoot
Write-Output "[windows-launcher] python=$python"
Write-Output "[windows-launcher] repo=$RepoRoot port=$Port log_level=$($env:LOG_LEVEL)"
$args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$Port", "--no-use-colors", "--log-level", $env:LOG_LEVEL)
if ($AccessLogEnabled.ToLowerInvariant() -ne "true") {
    $args += "--no-access-log"
}

& $python @args
exit $LASTEXITCODE
