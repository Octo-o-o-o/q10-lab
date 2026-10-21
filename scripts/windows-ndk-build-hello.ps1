$ErrorActionPreference = "Stop"
$env:QNX_BASE = "C:\q10-lab\ndk\bbndk"
$env:QNX_HOST = "C:\q10-lab\ndk\bbndk\host_10_3_1_12\win32\x86"
$env:QNX_TARGET = "C:\q10-lab\ndk\bbndk\target_10_3_1_995\qnx6"
$env:QNX_DIR = $env:QNX_TARGET
$env:QNX_CONFIGURATION = Join-Path $env:LOCALAPPDATA "Research In Motion\BlackBerry Native SDK"
$env:MAKEFLAGS = "-I$($env:QNX_TARGET)\usr\include"
$env:CPUVARDIR = "armle-v7"
$env:PATH = "$($env:QNX_HOST)\usr\bin;$($env:PATH)"
$src = "C:\q10-lab\ndk\src\console"
Set-Location $src
Get-Process make, ln -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
foreach ($name in @("Makefile", "libconsole.so", "libconsole.so.1", "libconsole.so.1.0", "libconsole.so.1.0.0")) {
    if (Test-Path $name) { Remove-Item -Force $name }
}
if (Test-Path "o.le-v7") { Remove-Item -Recurse -Force "o.le-v7" }
& qmake.exe -spec blackberry-armv7le-qcc CONFIG+=device CONFIG+=release
if ($LASTEXITCODE -ne 0) { throw "qmake failed $LASTEXITCODE" }
# Full `make` hangs on QNX `rm -f` of versioned .so names. Compile objects only, then link.
$objs = @(
    "o.le-v7/.obj/main.o",
    "o.le-v7/.obj/applicationui.o",
    "o.le-v7/.obj/moc_applicationui.o"
)
& make.exe @objs
if ($LASTEXITCODE -ne 0) { throw "make objects failed $LASTEXITCODE" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\q10-lab\ndk\windows-ndk-link-console.ps1
if ($LASTEXITCODE -ne 0) { throw "link failed $LASTEXITCODE" }
Write-Output "MAKE_OK"
