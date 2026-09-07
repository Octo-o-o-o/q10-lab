# Windows later. Current lab host is macOS; source env-bb10.sh there.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here '..')
$candidates = @(
  (Join-Path $root 'tools\bb10\host_10_3_1_12\win32\x86\usr\bin'),
  'C:\bbndk\host_10_3_1_12\win32\x86\usr\bin'
)
foreach ($c in $candidates) {
  if (Test-Path (Join-Path $c 'blackberry-deploy.bat')) {
    $env:BB10_HOST_BIN = $c
    $env:PATH = "$c;$env:PATH"
    Write-Output "BB10_HOST_BIN=$c"
    return
  }
}
Write-Error 'BB10 host tools not found on Windows yet.'
