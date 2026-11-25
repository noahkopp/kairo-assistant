# Kairo installer for Windows 10/11.
#   irm https://raw.githubusercontent.com/noahkopp/kairo-assistant/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
$Repo = "https://github.com/noahkopp/kairo-assistant.git"
$Dir = if ($env:KAIRO_DIR) { $env:KAIRO_DIR } else { Join-Path $HOME "kairo-assistant" }

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

if (-not (Have "winget")) {
    Write-Host "This installer needs winget (App Installer). Get it from the Microsoft Store, then run this again."
    return
}

Step "Installing tools (Python, Git, GitHub Copilot CLI)"
if (-not (Have "py") -and -not (Have "python")) {
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
}
if (-not (Have "git")) {
    winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
}
if (-not (Have "copilot")) {
    winget install -e --id GitHub.Copilot --silent --accept-package-agreements --accept-source-agreements
}
Refresh-Path

Step "Downloading Kairo to $Dir"
if (Test-Path (Join-Path $Dir ".git")) {
    git -C $Dir pull -q --ff-only
} else {
    git clone -q $Repo $Dir
}

Step "Setting up Kairo"
& (Join-Path $Dir "kairo.cmd") --setup-only

Step "Sign in to GitHub Copilot (Kairo's brain)"
Write-Host "You need a GitHub account with Copilot; the free plan works."
Write-Host "Copilot will open now. Sign in if it asks, choose to TRUST this folder, then type /exit"
Read-Host "Press Enter to continue"
Push-Location $Dir
try { copilot } finally { Pop-Location }

Step "Gmail and Google Calendar (optional)"
$yn = Read-Host "Connect Gmail and Google Calendar now? Takes about 5 minutes. [y/N]"
if ($yn -match '^[Yy]') {
    & (Join-Path $Dir "kairo.cmd") --google
} else {
    Write-Host "Skipped. Connect it later by running: $Dir\kairo.cmd --google"
}

Write-Host "`nKairo is installed. Press the Windows key, type Kairo, press Enter to start talking." -ForegroundColor Green
