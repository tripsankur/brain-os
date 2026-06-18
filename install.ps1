# Brain OS install script (PowerShell) - resolves path tokens and copies skill files to ~/.claude/
# Usage: .\install.ps1 [-Config path\to\brain-os.config.json] [-DryRun]

param(
    [string]$Config = "",
    [switch]$DryRun
)

$RepoRoot = $PSScriptRoot
if (-not $Config) { $Config = Join-Path $RepoRoot "brain-os.config.json" }

if (-not (Test-Path $Config)) {
    Write-Error "Config not found at $Config`nCopy config\brain-os.config.example.json to brain-os.config.json and fill in your paths."
    exit 1
}

$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$VaultPath  = $cfg.vault_path
$ClaudeRaw  = $cfg.claude_install_path
$ClaudePath = $ClaudeRaw -replace '^~', $env:USERPROFILE

Write-Host "Brain OS Install"
Write-Host "================"
Write-Host "  Repo:   $RepoRoot"
Write-Host "  Vault:  $VaultPath"
Write-Host "  Claude: $ClaudePath"
if ($DryRun) { Write-Host "  Mode:   DRY RUN (no files written)" }
Write-Host ""

function Resolve-AndCopy {
    param([string]$Src, [string]$Dest)
    if ($DryRun) { Write-Host "  [dry-run] $Src -> $Dest"; return }
    $dir = Split-Path $Dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $content = Get-Content $Src -Raw -Encoding utf8
    $content = $content -replace [regex]::Escape('{{VAULT_PATH}}'),  $VaultPath
    $content = $content -replace [regex]::Escape('{{CLAUDE_PATH}}'), $ClaudePath
    $content = $content -replace [regex]::Escape('{{REPO_PATH}}'),   $RepoRoot
    Set-Content -Path $Dest -Value $content -Encoding utf8 -NoNewline
    Write-Host "  installed $Dest"
}

function Copy-AsIs {
    param([string]$Src, [string]$Dest)
    if ($DryRun) { Write-Host "  [dry-run] $Src -> $Dest"; return }
    $dir = Split-Path $Dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item $Src $Dest -Force
    Write-Host "  installed $Dest"
}

Write-Host "Installing brain subcommand..."
Resolve-AndCopy "$RepoRoot\core\brain.md" "$ClaudePath\commands\brain.md"

Write-Host ""
Write-Host "Installing brain subcommands..."
Get-ChildItem "$RepoRoot\core\subcommands\*.md" | ForEach-Object {
    Resolve-AndCopy $_.FullName "$ClaudePath\skills\brain\subcommands\$($_.Name)"
}

Write-Host ""
Write-Host "Installing modules..."
Get-ChildItem "$RepoRoot\modules\*\module.json" | ForEach-Object {
    $moduleJson = $_
    $moduleDir  = $moduleJson.DirectoryName
    $moduleCfg  = Get-Content $moduleJson.FullName -Raw | ConvertFrom-Json
    $moduleName = $moduleCfg.name

    if (-not $moduleName) {
        Write-Warning "Could not read name from $($moduleJson.FullName) - skipping"
        return
    }

    Write-Host ""
    Write-Host "  [$moduleName] orchestrator..."
    Resolve-AndCopy "$moduleDir\$moduleName.md" "$ClaudePath\commands\$moduleName.md"

    Write-Host "  [$moduleName] agents..."
    Get-ChildItem "$moduleDir\agents\*.md" -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-AsIs $_.FullName "$ClaudePath\skills\$moduleName\agents\$($_.Name)"
    }

    # Register module in vault modules registry
    if ($VaultPath -and (Test-Path $VaultPath)) {
        $moduleVersion = $moduleCfg.version
        $modulesReg    = Join-Path $VaultPath "Claude\modules.md"
        $today         = Get-Date -Format "yyyy-MM-dd"
        if (-not (Test-Path $modulesReg)) {
            $header = "# Installed Modules`n> Auto-managed by install.ps1. Do not edit manually.`n`n| module | version | installed | claude_path |`n|--------|---------|-----------|-------------|`n"
            Set-Content -Path $modulesReg -Value $header -Encoding utf8
        }
        # Remove stale row for this module (handles reinstall), then append fresh row
        $lines = Get-Content $modulesReg | Where-Object { $_ -notmatch "^\| $([regex]::Escape($moduleName)) " }
        Set-Content -Path $modulesReg -Value $lines -Encoding utf8
        Add-Content -Path $modulesReg -Value "| $moduleName | $moduleVersion | $today | $ClaudePath |" -Encoding utf8
        Write-Host "  [$moduleName] registered in $modulesReg"
    }
}

Write-Host ""
Write-Host "Done. Brain OS installed to $ClaudePath"
