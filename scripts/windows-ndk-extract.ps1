$ErrorActionPreference = "Stop"
$zips = "C:\q10-lab\ndk\zips"
$root = "C:\q10-lab\ndk\bbndk"
$log = "C:\q10-lab\ndk\logs\extract.log"

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"), $msg
    Add-Content -Path $log -Value $line
    Write-Output $line
}

New-Item -ItemType Directory -Force -Path $root | Out-Null
$order = @(
    "bbndk.win32.tools.10.3.1.12.zip",
    "bbndk.win32.libraries.10.3.1.995.zip",
    "bbndk.win32.qconfigmk.10.3.1.995.zip"
)
Log "BEGIN extract into $root"
foreach ($name in $order) {
    $zip = Join-Path $zips $name
    if (-not (Test-Path $zip)) { throw "missing $zip" }
    Log "TAR $name"
    & tar.exe -xf $zip -C $root
    if ($LASTEXITCODE -ne 0) { throw "tar failed $name" }
}
$envCmd = Join-Path $root "bbndk-env_10_3_1_995.cmd"
Copy-Item -Force "C:\q10-lab\ndk\bbndk-env_10_3_1_995.cmd" $envCmd
Log "WROTE $envCmd"
$qcc = Join-Path $root "host_10_3_1_12\win32\x86\usr\bin\qcc.exe"
$qmake = Join-Path $root "host_10_3_1_12\win32\x86\usr\bin\qmake.exe"
$pkg = Join-Path $root "host_10_3_1_12\win32\x86\usr\bin\blackberry-nativepackager.bat"
foreach ($p in @($qcc, $qmake, $pkg)) {
    if (Test-Path $p) { Log "HAVE $p" } else { Log "MISSING $p" }
}
Log "EXTRACT_OK"
