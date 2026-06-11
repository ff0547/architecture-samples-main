$ErrorActionPreference = "Stop"
. "$PSScriptRoot\..\config.ps1"

if (-not (Test-Path $ProjectRoot)) {
    throw "Android project directory not found: $ProjectRoot"
}

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

Push-Location $ProjectRoot
try {
    Write-Host "=== 1. Build original debug APK ==="
    & ".\gradlew.bat" ":app:assembleDebug"
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle build failed"
    }
}
finally {
    Pop-Location
}

$BuiltApk = Join-Path $ProjectRoot "app\build\outputs\apk\debug\app-debug.apk"

if (-not (Test-Path $BuiltApk)) {
    throw "APK not found: $BuiltApk"
}

Copy-Item $BuiltApk $OriginalApk -Force
Write-Host "Original APK copied to: $OriginalApk"
