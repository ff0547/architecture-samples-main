$ErrorActionPreference = "Stop"

& "$PSScriptRoot\scripts\01_build_original_apk.ps1"
& "$PSScriptRoot\scripts\02_decode_patch_rebuild.ps1"
& "$PSScriptRoot\scripts\03_sign_install_verify.ps1"

Write-Host ""
Write-Host "Finished."
Write-Host "$PSScriptRoot\work\rebuilt-signed.apk"
