$ErrorActionPreference = "Stop"
Get-Process make, ln -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
$env:QNX_HOST = "C:\q10-lab\ndk\bbndk\host_10_3_1_12\win32\x86"
$env:QNX_TARGET = "C:\q10-lab\ndk\bbndk\target_10_3_1_995\qnx6"
$env:PATH = "$($env:QNX_HOST)\usr\bin;$($env:PATH)"
$src = "C:\q10-lab\ndk\src\console"
Set-Location $src
$objs = @(
    "o.le-v7\.obj\main.o",
    "o.le-v7\.obj\applicationui.o",
    "o.le-v7\.obj\moc_applicationui.o"
)
foreach ($o in $objs) {
    if (-not (Test-Path $o)) { throw "missing $o" }
    Write-Output ("OBJ " + $o + " " + (Get-Item $o).Length)
}
$out = "o.le-v7\console.so"
if (Test-Path $out) { Remove-Item -Force $out }
$lib = "C:\q10-lab\ndk\bbndk\target_10_3_1_995\qnx6\armle-v7"
$qccArgs = @(
    "-Vgcc_ntoarmv7le",
    "-lang-c++",
    "-Wl,-rpath-link,$lib\lib",
    "-Wl,-rpath-link,$lib\usr\lib",
    "-Wl,-rpath-link,$lib\usr\lib\qt4\lib",
    "-Wl,-O1",
    "-Wl,-z,relro",
    "-Wl,-soname,console.so",
    "-shared",
    "-Wl,-z,now",
    "-o", $out
) + $objs + @(
    "-L$lib\usr\lib\bb1",
    "-L$lib\lib",
    "-L$lib\usr\lib",
    "-L$lib\usr\lib\qt4\lib",
    "-lbbdata",
    "-lbbcascades",
    "-lQtDeclarative",
    "-lQtScript",
    "-lQtSvg",
    "-lQtSql",
    "-lsqlite3",
    "-lz",
    "-lQtXmlPatterns",
    "-lQtGui",
    "-lQtNetwork",
    "-lsocket",
    "-lQtCore",
    "-lm",
    "-lbps"
)
Write-Output "QCC_LINK"
& qcc.exe @qccArgs
if ($LASTEXITCODE -ne 0) { throw "qcc link failed $LASTEXITCODE" }
& ntoarmv7-readelf.exe -h $out | Select-String -Pattern "Class|Machine|Type"
Write-Output ("LINK_OK " + (Get-Item $out).Length)
