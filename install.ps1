# SpeedTerm - Installateur Windows (PowerShell)
# Usage: irm https://raw.githubusercontent.com/YOUR_USERNAME/speedterm/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$GithubRepo = "YOUR_USERNAME/speedterm"

function Write-Cyan($msg)   { Write-Host $msg -ForegroundColor Cyan }
function Write-Green($msg)  { Write-Host $msg -ForegroundColor Green }
function Write-Yellow($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Red($msg)    { Write-Host $msg -ForegroundColor Red }

Write-Cyan "╔═══════════════════════════════════════════╗"
Write-Cyan "║   Installation de SpeedTerm (Windows)     ║"
Write-Cyan "╚═══════════════════════════════════════════╝"
Write-Host ""

# Vérifie Python
$pythonCmd = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $version = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $version -match "Python 3") {
            $pythonCmd = $candidate
            Write-Green "✓ Python détecté : $version (via '$candidate')"
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Yellow "⚠ Python n'est pas installé."
    Write-Host "Tentative d'installation via winget..."
    try {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        Write-Green "✓ Python installé. Veuillez redémarrer votre terminal puis relancer ce script."
        exit 0
    } catch {
        Write-Red "✗ Impossible d'installer Python automatiquement."
        Write-Host "Installez Python manuellement depuis : https://www.python.org/downloads/"
        Write-Host "Puis relancez cette commande."
        exit 1
    }
}

# Vérifie git (recommandé pour pip install git+...)
$hasGit = $false
try {
    & git --version | Out-Null
    if ($LASTEXITCODE -eq 0) { $hasGit = $true }
} catch {}

if (-not $hasGit) {
    Write-Yellow "⚠ Git n'est pas détecté. Installation via archive ZIP à la place."
    Write-Cyan "➜ Téléchargement de speedterm depuis GitHub..."
    $zipUrl = "https://github.com/$GithubRepo/archive/refs/heads/main.zip"
    $tempDir = Join-Path $env:TEMP "speedterm-install-$([guid]::NewGuid())"
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    $zipPath = Join-Path $tempDir "speedterm.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
    $extracted = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1
    Write-Cyan "➜ Installation via pip..."
    & $pythonCmd -m pip install --upgrade $extracted.FullName
    Remove-Item -Path $tempDir -Recurse -Force
} else {
    Write-Cyan "➜ Installation de speedterm depuis GitHub..."
    & $pythonCmd -m pip install --upgrade "git+https://github.com/$GithubRepo.git"
}

if ($LASTEXITCODE -ne 0) {
    Write-Red "✗ Installation échouée."
    exit 1
}

Write-Host ""
Write-Green "╔═══════════════════════════════════════════╗"
Write-Green "║   ✓ Installation réussie !                ║"
Write-Green "╚═══════════════════════════════════════════╝"
Write-Host ""

# Vérifie que la commande est dans le PATH
$cmd = Get-Command speedterm -ErrorAction SilentlyContinue
if ($cmd) {
    Write-Host "Lancez la commande : " -NoNewline
    Write-Cyan "speedterm"
} else {
    Write-Yellow "⚠ La commande 'speedterm' n'est pas dans votre PATH."
    Write-Host "Vous pouvez la lancer via : " -NoNewline
    Write-Cyan "$pythonCmd -m speedterm"
    Write-Host ""
    Write-Host "Ou ajoutez le dossier des Scripts Python à votre PATH."
}
