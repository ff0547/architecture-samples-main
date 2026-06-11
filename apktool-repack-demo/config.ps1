$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\fsqfs\Desktop\architecture-samples-main"
$ApktoolBat = "C:\tools\apktool\apktool.bat"

$AndroidSdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
$Adb = Join-Path $AndroidSdk "platform-tools\adb.exe"

$BuildToolsRoot = Join-Path $AndroidSdk "build-tools"
$LatestBuildTools = Get-ChildItem $BuildToolsRoot -Directory |
    Sort-Object { [version]$_.Name } -Descending |
    Select-Object -First 1

if (-not $LatestBuildTools) {
    throw "未找到 Android SDK Build Tools：$BuildToolsRoot"
}

$Zipalign = Join-Path $LatestBuildTools.FullName "zipalign.exe"
$Apksigner = Join-Path $LatestBuildTools.FullName "apksigner.bat"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkDir = Join-Path $RepoRoot "work"
$OriginalApk = Join-Path $WorkDir "original.apk"
$DecodedDir = Join-Path $WorkDir "decoded"
$UnsignedApk = Join-Path $WorkDir "rebuilt-unsigned.apk"
$AlignedApk = Join-Path $WorkDir "rebuilt-aligned.apk"
$SignedApk = Join-Path $WorkDir "rebuilt-signed.apk"

$Keystore = Join-Path $RepoRoot "demo.keystore"
$KeyAlias = "apktool-demo"
$StorePass = "android"
$KeyPass = "android"

$ModifiedAppName = "TODO APKTool Modified"
