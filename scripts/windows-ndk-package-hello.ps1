$ErrorActionPreference = "Stop"
$env:QNX_HOST = "C:\q10-lab\ndk\bbndk\host_10_3_1_12\win32\x86"
$env:QNX_TARGET = "C:\q10-lab\ndk\bbndk\target_10_3_1_995\qnx6"
$env:PATH = "$($env:QNX_HOST)\usr\bin;$($env:PATH)"
$src = "C:\q10-lab\ndk\src\console"
Set-Location $src
$so = Join-Path $src "o.le-v7\console.so"
if (-not (Test-Path $so)) { throw "missing $so" }
& ntoarmv7-readelf.exe -h $so | Select-String -Pattern "Class|Machine"
$bar = "C:\q10-lab\ndk\console-0.0.2.bar"
if (Test-Path $bar) { Remove-Item $bar }
$lib = Join-Path $env:QNX_HOST "usr\lib"
$cp = @(
    "EccpressoJDK15ECC.jar", "EccpressoAll.jar", "TrustpointAll.jar",
    "TrustpointJDK15.jar", "TrustpointProviders.jar", "BarPackager.jar",
    "BarSigner.jar", "BarDeploy.jar", "BarAir.jar"
) | ForEach-Object { Join-Path $lib $_ }
$java17 = "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin\java.exe"
if (-not (Test-Path $java17)) { throw "need Java 17 at $java17" }
Remove-Item Env:JAVA_TOOL_OPTIONS -ErrorAction SilentlyContinue
$argsJava = @(
    "-Djava.awt.headless=true",
    "--add-opens=java.xml/com.sun.org.apache.xerces.internal.parsers=ALL-UNNAMED",
    "--add-opens=java.xml/com.sun.org.apache.xerces.internal.util=ALL-UNNAMED",
    "--add-opens=java.xml/com.sun.org.apache.xerces.internal.xni=ALL-UNNAMED",
    "--add-opens=java.xml/com.sun.org.apache.xerces.internal.xni.parser=ALL-UNNAMED",
    "--add-opens=java.xml/com.sun.org.apache.xerces.internal.jaxp=ALL-UNNAMED",
    "--add-opens=java.base/java.lang=ALL-UNNAMED",
    "-Xmx512M",
    "-cp", ($cp -join ";"),
    "com.qnx.bbt.nativepackager.BarNativePackager",
    "-devMode",
    "-package", $bar,
    "bar-descriptor.xml",
    "-e", $so, "console.so",
    "-e", (Join-Path $src "icon.png"), "icon.png",
    "-e", (Join-Path $src "assets\main.qml"), "assets/main.qml",
    "-e", (Join-Path $src "assets\projection.json"), "assets/projection.json"
)
& $java17 @argsJava
if ($LASTEXITCODE -ne 0) {
    throw "packager failed $LASTEXITCODE"
}
Get-Item $bar | Format-List Name, Length, LastWriteTime
Write-Output "BAR_OK"
