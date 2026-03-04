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

function Test-PortAvailability {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        return $false
    }
    return $true
}

function Run-PreflightChecks {
    param([int]$Port, [string]$LogLevel, [string]$ApiKey, [string]$PythonExe)

    Write-Host ""
    Write-Host "================= PREFLIGHT CHECKS ================="

    $critCount = 0
    $warnCount = 0

    # 1. Port Check
    $portFree = Test-PortAvailability -Port $Port
    if ($portFree) {
        Write-Host "[OK]   Port $Port is available" -ForegroundColor Green
    } else {
        Write-Host "[CRIT] Port $Port is already in use by another process" -ForegroundColor Red
        $critCount++
    }

    # 2. Log Level
    $validLevels = @("critical", "error", "warning", "info", "debug", "trace")
    if ($validLevels -contains $LogLevel.ToLowerInvariant()) {
        Write-Host "[OK]   Log level '$LogLevel' is valid" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Log level '$LogLevel' is unrecognized, uvicorn may fail" -ForegroundColor Yellow
        $warnCount++
    }

    # 3. API Key
    if ($ApiKey -eq "change-me") {
        Write-Host "[WARN] MT5_BRIDGE_API_KEY is using the default 'change-me'" -ForegroundColor Yellow
        $warnCount++
    } else {
        Write-Host "[OK]   API Key configured securely" -ForegroundColor Green
    }

    # 4. Python checks
    $pyVersion = & $PythonExe -c "import platform; print(platform.python_version())" 2>$null
    if ($LASTEXITCODE -eq 0 -and $pyVersion) {
        Write-Host "[OK]   Python $pyVersion discovered at $PythonExe" -ForegroundColor Green
    } else {
        Write-Host "[CRIT] Python executable invalid or failing" -ForegroundColor Red
        $critCount++
    }

    Write-Host "Preflight complete: $critCount CRITICAL, $warnCount WARNINGS"
    Write-Host "===================================================="
    Write-Host ""

    if ($critCount -gt 0) {
        Write-Host "Preflight critical failures. Aborting launch." -ForegroundColor Red
        exit 1
    }
}

function Print-FailureDiagnostic {
    param([string]$OutputContent)

    Write-Host ""
    Write-Host "==== BRIDGE STARTUP FAILURE DIAGNOSTICS ====" -ForegroundColor Red
    
    if ($OutputContent -match "error while attempting to bind on address") {
        Write-Host "Diagnosis  : Port Conflict Detected" -ForegroundColor Yellow
        Write-Host "Resolution : The port is already strictly bound by another process. Check 'stop_bridge' or your task manager."
    }
    elseif ($OutputContent -match "ModuleNotFoundError") {
        Write-Host "Diagnosis  : Missing Python Dependency" -ForegroundColor Yellow
        Write-Host "Resolution : Ensure all requirements are installed in the venv."
    }
    elseif ($OutputContent -match "ValidationError") {
        Write-Host "Diagnosis  : Environment Validation Failed" -ForegroundColor Yellow
        Write-Host "Resolution : Check your .env file limits (e.g., config types)."
    }
    elseif ($OutputContent -match "MetaTrader5.initialize\(\) failed") {
        Write-Host "Diagnosis  : MT5 Terminal Launch Failure" -ForegroundColor Yellow
        Write-Host "Resolution : Verify MT5 is installed and reachable by the bridge."
    }
    else {
        Write-Host "Diagnosis  : Unknown Startup Traceback" -ForegroundColor Yellow
        Write-Host "Resolution : Review the output above for clues."
    }

    Write-Host "===========================================" -ForegroundColor Red
    Write-Host ""
}

$SkipPreflight = ($env:LAUNCHER_SKIP_PREFLIGHT -eq "true" -or $env:LAUNCHER_SKIP_PREFLIGHT -eq "1")

if (-not $SkipPreflight) {
    Run-PreflightChecks -Port $Port -LogLevel $env:LOG_LEVEL -ApiKey $env:MT5_BRIDGE_API_KEY -PythonExe $python
}

Set-Location $RepoRoot
Write-Output "[windows-launcher] python=$python"
Write-Output "[windows-launcher] repo=$RepoRoot port=$Port log_level=$($env:LOG_LEVEL)"
$args = @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$Port", "--no-use-colors", "--log-level", $env:LOG_LEVEL)
if ($AccessLogEnabled.ToLowerInvariant() -ne "true") {
    $args += "--no-access-log"
}

# Run the bridge and capture output to display diagnostics
$combinedOutput = ""
& $python @args 2>&1 | ForEach-Object {
    $combinedOutput += "$_`n"
    Write-Output $_
}

if ($LASTEXITCODE -ne 0) {
    Print-FailureDiagnostic -OutputContent $combinedOutput
}
exit $LASTEXITCODE
