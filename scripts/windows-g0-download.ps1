$ErrorActionPreference = "Stop"
$destDir = "C:\q10-lab\g0"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$name = "Q10_10.3.03.3216_SQN100-1-2-3-4-5.7z"
$dest = Join-Path $destDir $name
$expectSize = 1569051774
$expectMd5 = "ba16ec5a1405611897ca04473c6160a7"
$expectSha1 = "56fca640c73f9ed042b6dd29c719f1f43fcea1c9"
$expectSha256 = "1cd4d70fe2fd0ebc7155d54deeb6cc4b45cc74b75dca76305a6fe6ffd7cec1e4"

Write-Output "G0 dest $destDir"
Write-Output "lunarproject.org is parked (GoDaddy) as of 2026-09-15; curl cannot fetch the 7z."
Write-Output "Live folder: https://mega.nz/folder/ERomDKaT#YYXwe5p2bUlm_4VW5VfTtw"
Write-Output "Put $name (and optionally !10.3.3.3216_OSINFO!.txt) here, then re-run this script."

if (-not (Test-Path $dest)) {
    Write-Output "G0_WAITING_FILE"
    exit 2
}

$got = (Get-Item $dest).Length
Write-Output "HAVE size=$got"
if ($got -ne $expectSize) { throw "size mismatch: got $got expected $expectSize" }

function Hash-File([string]$path, [string]$alg) {
    return (Get-FileHash -Algorithm $alg -Path $path).Hash.ToLowerInvariant()
}
$md5 = Hash-File $dest "MD5"
$sha1 = Hash-File $dest "SHA1"
$sha256 = Hash-File $dest "SHA256"
Write-Output "MD5 $md5"
Write-Output "SHA1 $sha1"
Write-Output "SHA256 $sha256"
if ($md5 -ne $expectMd5) { throw "MD5 mismatch" }
if ($sha1 -ne $expectSha1) { throw "SHA1 mismatch" }
if ($sha256 -ne $expectSha256) { throw "SHA256 mismatch" }
Write-Output "G0_VERIFY_OK $dest"
