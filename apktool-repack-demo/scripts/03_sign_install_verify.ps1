$ErrorActionPreference = "Stop"
. "$PSScriptRoot\..\config.ps1"

foreach ($Tool in @($Adb, $Zipalign, $Apksigner)) {
    if (-not (Test-Path $Tool)) {
        throw "Tool not found: $Tool"
    }
}

if (-not (Test-Path $UnsignedApk)) {
    throw "Unsigned APK not found: $UnsignedApk"
}

Write-Host "=== 5. Create local test keystore if required ==="

if (-not (Test-Path $Keystore)) {
    & keytool -genkeypair `
        -keystore $Keystore `
        -storepass $StorePass `
        -keypass $KeyPass `
        -alias $KeyAlias `
        -keyalg RSA `
        -keysize 2048 `
        -validity 3650 `
        -dname "CN=APKTool Demo, OU=Course, O=Local, L=Tokyo, ST=Tokyo, C=JP"

    if ($LASTEXITCODE -ne 0) {
        throw "Keystore creation failed"
    }
}

Write-Host "=== 6. Run zipalign ==="

Remove-Item $AlignedApk -Force -ErrorAction SilentlyContinue

& $Zipalign -f -p 4 $UnsignedApk $AlignedApk

if ($LASTEXITCODE -ne 0) {
    throw "zipalign failed"
}

Write-Host "=== 7. Sign APK ==="

Remove-Item $SignedApk -Force -ErrorAction SilentlyContinue

& $Apksigner sign `
    --ks $Keystore `
    --ks-key-alias $KeyAlias `
    --ks-pass "pass:$StorePass" `
    --key-pass "pass:$KeyPass" `
    --out $SignedApk `
    $AlignedApk

if ($LASTEXITCODE -ne 0) {
    throw "APK signing failed"
}

Write-Host "=== 8. Verify APK signature ==="

$VerifyFile = Join-Path $WorkDir "verify.txt"

& $Apksigner verify --verbose --print-certs $SignedApk |
    Tee-Object -FilePath $VerifyFile

if ($LASTEXITCODE -ne 0) {
    throw "APK signature verification failed"
}

Write-Host "=== 9. Read package name ==="

$Manifest = Join-Path $DecodedDir "AndroidManifest.xml"
$ManifestText = [System.IO.File]::ReadAllText($Manifest)

if ($ManifestText -notmatch 'package="([^"]+)"') {
    throw "Package name not found in AndroidManifest.xml"
}

$PackageName = $Matches[1]

Write-Host "Package name: $PackageName"

Write-Host "=== 10. Install rebuilt APK ==="

& $Adb uninstall $PackageName | Out-Host
& $Adb install $SignedApk

if ($LASTEXITCODE -ne 0) {
    throw "ADB install failed"
}

Write-Host "=== 11. Launch application ==="

& $Adb shell monkey -p $PackageName -c android.intent.category.LAUNCHER 1

Write-Host ""
Write-Host "Verification finished."
Write-Host "Signed APK: $SignedApk"
Write-Host "Expected application label: $ModifiedAppName"
Write-Host "Signature verification log: $VerifyFile"
