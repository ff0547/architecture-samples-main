$ErrorActionPreference = "Stop"
. "$PSScriptRoot\..\config.ps1"

if (-not (Test-Path $ApktoolBat)) {
    throw "APKTool not found: $ApktoolBat"
}

if (-not (Test-Path $OriginalApk)) {
    throw "Original APK not found: $OriginalApk"
}

if (Test-Path $DecodedDir) {
    Remove-Item $DecodedDir -Recurse -Force
}

Remove-Item $UnsignedApk -Force -ErrorAction SilentlyContinue

Write-Host "=== 2. Decode APK with APKTool ==="
& $ApktoolBat d -f $OriginalApk -o $DecodedDir

if ($LASTEXITCODE -ne 0) {
    throw "APKTool decode failed"
}

$Manifest = Join-Path $DecodedDir "AndroidManifest.xml"

if (-not (Test-Path $Manifest)) {
    throw "AndroidManifest.xml not found"
}

Write-Host "=== 3. Patch application label ==="

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$ManifestText = [System.IO.File]::ReadAllText($Manifest)

if ($ManifestText -match 'android:label="[^"]*"') {
    $ManifestText = [regex]::Replace(
        $ManifestText,
        'android:label="[^"]*"',
        ('android:label="' + $ModifiedAppName + '"'),
        1
    )
}
else {
    throw "android:label was not found in AndroidManifest.xml"
}

[System.IO.File]::WriteAllText($Manifest, $ManifestText, $Utf8NoBom)

$StringsXml = Join-Path $DecodedDir "res\values\strings.xml"

if (Test-Path $StringsXml) {
    $StringsText = [System.IO.File]::ReadAllText($StringsXml)

    if ($StringsText -match '<string name="app_name">.*?</string>') {
        $StringsText = [regex]::Replace(
            $StringsText,
            '<string name="app_name">.*?</string>',
            ('<string name="app_name">' + $ModifiedAppName + '</string>'),
            1
        )

        [System.IO.File]::WriteAllText($StringsXml, $StringsText, $Utf8NoBom)
    }
}

Write-Host "New application label: $ModifiedAppName"

Write-Host "=== 4. Rebuild unsigned APK ==="
& $ApktoolBat b $DecodedDir -o $UnsignedApk

if ($LASTEXITCODE -ne 0) {
    throw "APKTool rebuild failed"
}

Write-Host "Unsigned APK created: $UnsignedApk"
