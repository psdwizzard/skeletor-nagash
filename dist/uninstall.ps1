# Skeletor Nagash - Windows uninstaller.
# Finds skeletor_nagash.pack in the TWW3 data folder and removes it.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms | Out-Null

$packName = 'skeletor_nagash.pack'
$title = 'Skeletor Nagash Uninstaller'

function Show($msg, $icon = 'Information') {
    [System.Windows.Forms.MessageBox]::Show($msg, $title, 'OK', $icon) | Out-Null
}

# --- find the installed pack (same detection as the installer) --------------
$gameRel = 'steamapps\common\Total War WARHAMMER III\data'
$roots = New-Object System.Collections.Generic.List[string]
$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
if ($steam) { $roots.Add(($steam -replace '/', '\')) }
$roots.Add('C:\Program Files (x86)\Steam')
$roots.Add('C:\Program Files\Steam')
foreach ($r in @($roots.ToArray())) {
    $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
    if (Test-Path $vdf) {
        foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
            $roots.Add(($m.Groups[1].Value -replace '\\\\', '\'))
        }
    }
}

$target = $null
foreach ($r in $roots | Select-Object -Unique) {
    $p = Join-Path (Join-Path $r $gameRel) $packName
    if (Test-Path $p) { $target = $p; break }
}

if (-not $target) {
    $ans = [System.Windows.Forms.MessageBox]::Show(
        "Couldn't find an installed $packName automatically.`n`nPick the game's 'data' folder yourself?",
        $title, 'YesNo', 'Question')
    if ($ans -ne 'Yes') { exit 0 }
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select the game's data folder (...\Total War WARHAMMER III\data)"
    if ($dlg.ShowDialog() -ne 'OK') { exit 0 }
    $target = Join-Path $dlg.SelectedPath $packName
    if (-not (Test-Path $target)) {
        Show "No $packName in that folder - the mod isn't installed there." 'Warning'
        exit 0
    }
}

$ans = [System.Windows.Forms.MessageBox]::Show(
    "Remove the Skeletor voice mod?`n`n$target`n`nNagash's original voice returns immediately.",
    $title, 'YesNo', 'Question')
if ($ans -ne 'Yes') { exit 0 }

# --- delete, elevating once if write-protected ------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
try {
    Remove-Item $target -Force
} catch {
    if (-not $isAdmin) {
        Start-Process powershell -Verb RunAs -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA', '-File', "`"$PSCommandPath`"")
        exit 0
    }
    Show "Delete failed even as administrator:`n$($_.Exception.Message)" 'Error'
    exit 1
}

Show "Uninstalled. Nagash sounds like Nagash again.`n(Re-run install.bat any time to bring Skeletor back.)"
exit 0
