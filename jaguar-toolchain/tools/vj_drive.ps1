# vj_drive.ps1 - launch Virtual Jaguar on a ROM, press keys, capture the window.
# Usage: powershell -File tools\vj_drive.ps1 -Rom gate7_castle\gate7_castle.cof -Out shots -Script "wait:3;shot:boot;hold:C:800;shot:right"
#   wait:<s>          sleep seconds
#   hold:<key>:<ms>   hold a key (Z C S X L ...) for ms
#   tap:<key>         press and release
#   shot:<name>       save <Out>\<name>.png of the emulator window
param(
    [Parameter(Mandatory = $true)][string]$Rom,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Script = "wait:4;shot:boot",
    [string]$Exe = "C:\Users\Owner\.bob\playground\jaguar-toolchain\emulator\vjaguar\virtualjaguar.exe",
    [switch]$KeepOpen
)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
New-Item -ItemType Directory -Force $Out | Out-Null
$romPath = (Resolve-Path $Rom).Path
# Guard: a Jaguar COFF starts 01 50 and enters at $802000 (header bytes 36..39).
$hdr = [System.IO.File]::ReadAllBytes($romPath)
if ($romPath -like "*.cof") {
    $entry = ($hdr[36] -shl 24) -bor ($hdr[37] -shl 16) -bor ($hdr[38] -shl 8) -bor $hdr[39]
    if ($hdr.Length -lt 48 -or $hdr[0] -ne 0x01 -or $hdr[1] -ne 0x50 -or $entry -ne 0x802000) {
        throw ("refusing {0}: not a Jaguar COFF (first bytes {1:X2} {2:X2}, entry `${3:X6}). Restore it with git restore or rebuild; never write binaries with PowerShell '>'." -f $romPath, $hdr[0], $hdr[1], $entry)
    }
}
$p = Start-Process -FilePath $Exe -ArgumentList "`"$romPath`"" -WorkingDirectory (Split-Path $Exe) -PassThru
$h = [IntPtr]::Zero
for ($i = 0; $i -lt 50 -and $h -eq [IntPtr]::Zero; $i++) {
    Start-Sleep -Milliseconds 200
    $p.Refresh()
    $h = $p.MainWindowHandle
}
if ($h -eq [IntPtr]::Zero) { throw "Virtual Jaguar window not found" }

function Focus { [W]::ShowWindow($h, 9) | Out-Null; [W]::SetForegroundWindow($h) | Out-Null; Start-Sleep -Milliseconds 150 }
function Key([string]$k, [bool]$down) {
    if ($k -match '^F(\d+)$') { $vk = [byte](0x6F + [int]$Matches[1]) } else { $vk = [byte][char]$k.ToUpper() }
    $scan = [byte][W]::MapVirtualKey($vk, 0)
    $flags = if ($down) { 0 } else { 2 }
    [W]::keybd_event($vk, $scan, $flags, [UIntPtr]::Zero)
}
function Shot([string]$name) {
    $r = New-Object W+RECT
    [W]::GetWindowRect($h, [ref]$r) | Out-Null
    $w = $r.R - $r.L; $hh = $r.B - $r.T
    $bmp = New-Object System.Drawing.Bitmap $w, $hh
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
    $bmp.Save((Join-Path $Out "$name.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Output "shot $name ($w x $hh)"
}

Focus
foreach ($step in $Script.Split(';')) {
    $a = $step.Split(':')
    switch ($a[0]) {
        "wait" { Start-Sleep -Milliseconds ([int]([double]$a[1] * 1000)) }
        "hold" { Focus; Key $a[1] $true; Start-Sleep -Milliseconds ([int]$a[2]); Key $a[1] $false }
        "tap"  { Focus; Key $a[1] $true; Start-Sleep -Milliseconds 80; Key $a[1] $false; Start-Sleep -Milliseconds 80 }
        "shot" { Focus; Shot $a[1] }
        "burst" { Focus; for ($n = 0; $n -lt [int]$a[2]; $n++) { Shot ("{0}_{1}" -f $a[1], $n); Start-Sleep -Milliseconds 120 } }
    }
}
if (-not $KeepOpen) { Stop-Process -Id $p.Id -Force }
