# workbench-ai installer — PowerShell
# Usage: irm https://raw.githubusercontent.com/TheRealDataBoss/workbench/main/installer/install.ps1 | iex

$ErrorActionPreference = "Stop"

$WorkbenchHome = Join-Path $env:USERPROFILE ".workbench"
$WorkbenchBin  = Join-Path $WorkbenchHome "bin"
$WorkbenchSrc  = Join-Path $WorkbenchHome "src"
$RepoUrl       = "https://github.com/TheRealDataBoss/workbench.git"
$Version       = "0.1.0"

function Write-Info  { param($Msg) Write-Host "[workbench] $Msg" -ForegroundColor Cyan }
function Write-Ok    { param($Msg) Write-Host "[workbench] $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[workbench] $Msg" -ForegroundColor Yellow }

function Test-Command {
    param($Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# --- Check prerequisites ---

Write-Info "workbench-ai installer v$Version"
Write-Info "================================="

if (-not (Test-Command "git")) {
    Write-Error "git is required but not found. Install git and retry."
    exit 1
}
Write-Info "git: $(git --version)"

if (Test-Command "node") {
    Write-Info "node: $(node --version)"
} else {
    Write-Warn "node not found. npm CLI will not be available. Install Node.js 18+ for full functionality."
}

if (Test-Command "python") {
    Write-Info "python: $(python --version 2>&1)"
} else {
    Write-Warn "python not found. Python CLI will not be available. Install Python 3.10+ for full functionality."
}

# --- Install ---

Write-Info "Installing workbench-ai v$Version to $WorkbenchHome"

if (Test-Path $WorkbenchSrc) {
    Write-Info "Existing installation found. Updating..."
    Push-Location $WorkbenchSrc
    git pull --ff-only origin main
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Error "Failed to update workbench-ai. Check your network connection."
        exit 1
    }
    Pop-Location
} else {
    New-Item -ItemType Directory -Force -Path $WorkbenchHome | Out-Null
    New-Item -ItemType Directory -Force -Path $WorkbenchBin  | Out-Null

    Write-Info "Cloning workbench-ai repository..."
    git clone --depth 1 $RepoUrl $WorkbenchSrc
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to clone repository. Check your network connection."
        exit 1
    }
}

# Create bin wrapper script
$WrapperPath = Join-Path $WorkbenchBin "workbench.ps1"
$WrapperContent = @'
$WorkbenchSrc = Join-Path $env:USERPROFILE ".workbench\src"
if (Get-Command node -ErrorAction SilentlyContinue) {
    & node (Join-Path $WorkbenchSrc "packages\npm\bin\workbench.js") @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m workbench_ai.cli @args
} else {
    Write-Error "workbench-ai requires Node.js 18+ or Python 3.10+"
    exit 1
}
'@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding UTF8

# Create cmd wrapper for non-PowerShell terminals
$CmdWrapperPath = Join-Path $WorkbenchBin "workbench.cmd"
$CmdContent = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0workbench.ps1`" %*"
Set-Content -Path $CmdWrapperPath -Value $CmdContent -Encoding UTF8

Write-Ok "Binary installed to $WorkbenchBin"

# --- Update PATH ---

$CurrentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentUserPath -notlike "*$WorkbenchBin*") {
    $NewPath = "$WorkbenchBin;$CurrentUserPath"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Ok "Added $WorkbenchBin to user PATH"
} else {
    Write-Info "PATH already contains $WorkbenchBin"
}

# Add to current session
if ($env:Path -notlike "*$WorkbenchBin*") {
    $env:Path = "$WorkbenchBin;$env:Path"
}

# --- Verify ---

if (Test-Command "workbench") {
    Write-Ok "Installation verified: workbench is on PATH"
} else {
    Write-Warn "workbench is installed but may not be on PATH until you restart your terminal."
}

Write-Host ""
Write-Ok "workbench-ai v$Version installed successfully!"
Write-Host ""
Write-Info "Next steps:"
Write-Info "  1. cd into your project directory"
Write-Info "  2. Run: workbench init"
Write-Info "  3. Run: workbench sync"
Write-Host ""
Write-Info "Documentation: https://github.com/TheRealDataBoss/workbench"
