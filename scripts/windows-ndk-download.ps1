$ErrorActionPreference = "Stop"
$dest = "C:\q10-lab\ndk\zips"
$log = "C:\q10-lab\ndk\logs\download.log"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
New-Item -ItemType Directory -Force -Path "C:\q10-lab\ndk\logs" | Out-Null

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"), $msg
    Add-Content -Path $log -Value $line
    Write-Output $line
}

$files = @(
    @{
        name = "bbndk.win32.qconfigmk.10.3.1.995.zip"
        size = 5492
        md5  = "9eb2917691dbbc1bbe1383cf4c885e2b"
        sha1 = "484046c6dc3b831f9581530826e00f1b1c3ac317"
    },
    @{
        name = "bbndk.win32.tools.10.3.1.12.zip"
        size = 304910772
        md5  = "dbaa70183be61f06b418702a9ffbbb8e"
        sha1 = "177fdd6ebb611802e9919398a159cde21d6d8fe8"
    },
    @{
        name = "bbndk.win32.libraries.10.3.1.995.zip"
        size = 1607600440
        md5  = "53d09d60a27b4c13edc464b5bd8f72b7"
        sha1 = "6a48b68b8e891656eb18083b06eb42192e0d8093"
    }
)

Log "BEGIN download to $dest"
foreach ($f in $files) {
    $url = "https://archive.org/download/bbdevtools/$($f.name)"
    $out = Join-Path $dest $f.name
    if ((Test-Path $out) -and ((Get-Item $out).Length -eq $f.size)) {
        Log "HAVE $($f.name) size already $($f.size)"
    }
    else {
        Log "CURL $($f.name)"
        & curl.exe -L --retry 5 --retry-all-errors -C - --output $out $url
        if ($LASTEXITCODE -ne 0) {
            throw "curl failed $($f.name) exit $LASTEXITCODE"
        }
    }
    $len = (Get-Item $out).Length
    if ($len -ne $f.size) {
        throw "size mismatch $($f.name) $len != $($f.size)"
    }
    $sha1 = (Get-FileHash $out -Algorithm SHA1).Hash.ToLower()
    if ($sha1 -ne $f.sha1) {
        throw "sha1 mismatch $($f.name) $sha1"
    }
    $md5 = (Get-FileHash $out -Algorithm MD5).Hash.ToLower()
    if ($md5 -ne $f.md5) {
        throw "md5 mismatch $($f.name) $md5"
    }
    $sha256 = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
    Log "OK $($f.name) sha256=$sha256"
}
Log "ALL_OK"
