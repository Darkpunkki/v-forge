param(
    [string]$OutDir = "ssl",
    [string]$CertFile = "cert.pem",
    [string]$KeyFile = "key.pem",
    [int]$Days = 365
)

$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    $fallbacks = @(
        "$env:ProgramFiles\Git\usr\bin\openssl.exe",
        "$env:ProgramFiles(x86)\Git\usr\bin\openssl.exe"
    )
    foreach ($candidate in $fallbacks) {
        if (Test-Path $candidate) {
            $openssl = $candidate
            break
        }
    }
}

if (-not $openssl) {
    Write-Error "openssl not found on PATH (or Git for Windows). Install OpenSSL and retry."
    exit 1
}

$fullOutDir = Resolve-Path -Path $OutDir -ErrorAction SilentlyContinue
if (-not $fullOutDir) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    $fullOutDir = Resolve-Path -Path $OutDir
}

$certPath = Join-Path $fullOutDir $CertFile
$keyPath = Join-Path $fullOutDir $KeyFile

if ($openssl -is [string]) {
    $opensslPath = $openssl
} else {
    $opensslPath = $openssl.Path
}

& $opensslPath req -x509 -newkey rsa:2048 -sha256 -days $Days -nodes `
    -subj "/CN=localhost" -keyout $keyPath -out $certPath

Write-Host "Generated certificate: $certPath"
Write-Host "Generated key: $keyPath"
