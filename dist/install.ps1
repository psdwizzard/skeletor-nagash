# Skeletor Nagash - Windows installer.
# Finds the TWW3 data folder (Steam registry + every Steam library), copies the
# pack, and opens Explorer on the installed file. Falls back to a folder picker.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms | Out-Null

$packName = 'skeletor_nagash.pack'
$pack = Join-Path $PSScriptRoot $packName
$title = 'Skeletor Nagash Installer'

function Show($msg, $icon = 'Information') {
    [System.Windows.Forms.MessageBox]::Show($msg, $title, 'OK', $icon) | Out-Null
}

if (-not (Test-Path $pack)) {
    Show "Can't find $packName next to this installer.`nExtract the whole zip first, then run install.bat from the extracted folder." 'Error'
    exit 1
}

# --- find the game's data folder -------------------------------------------
$gameRel = 'steamapps\common\Total War WARHAMMER III\data'
$roots = New-Object System.Collections.Generic.List[string]
$steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
if ($steam) { $roots.Add(($steam -replace '/', '\')) }
$roots.Add('C:\Program Files (x86)\Steam')
$roots.Add('C:\Program Files\Steam')

# add every Steam library folder listed in libraryfolders.vdf
foreach ($r in @($roots.ToArray())) {
    $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
    if (Test-Path $vdf) {
        foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
            $roots.Add(($m.Groups[1].Value -replace '\\\\', '\'))
        }
    }
}

$dest = $null
foreach ($r in $roots | Select-Object -Unique) {
    $d = Join-Path $r $gameRel
    if (Test-Path $d) { $dest = $d; break }
}

if (-not $dest) {
    Show "Couldn't find Total War: WARHAMMER III automatically.`n`nIn the next window, select the game's 'data' folder:`n...\Steam\steamapps\common\Total War WARHAMMER III\data"
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select the game's data folder (...\Total War WARHAMMER III\data)"
    if ($dlg.ShowDialog() -ne 'OK') { exit 1 }
    $dest = $dlg.SelectedPath
    # be forgiving if they picked the game folder instead of data
    if ((Split-Path $dest -Leaf) -ne 'data' -and (Test-Path (Join-Path $dest 'data'))) {
        $dest = Join-Path $dest 'data'
    }
}

# --- copy, elevating once if the folder is write-protected ------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
try {
    Copy-Item $pack (Join-Path $dest $packName) -Force
} catch {
    if (-not $isAdmin) {
        Start-Process powershell -Verb RunAs -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA', '-File', "`"$PSCommandPath`"")
        exit 0
    }
    Show "Copy failed even as administrator:`n$($_.Exception.Message)" 'Error'
    exit 1
}

Start-Process explorer.exe "/select,`"$(Join-Path $dest $packName)`""
Show "Installed!`n`n$packName is now in:`n$dest`n`nJust launch the game - no mod manager needed.`nTo uninstall, delete that file."
exit 0
