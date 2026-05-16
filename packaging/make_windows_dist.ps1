param(
    [string]$Name = "ARM32TeachingSimulator-Windows"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SpecPath = Join-Path $ProjectRoot "packaging\pyinstaller\sim.spec"
$PyInstallerDist = Join-Path $ProjectRoot "dist\sim"
$FinalRoot = Join-Path $ProjectRoot "packaging\dist\$Name"
$FinalZip = Join-Path $ProjectRoot "packaging\dist\$Name.zip"
$ToolchainBin = Join-Path $ProjectRoot "runtime\toolchain\bin"

if (-not (Test-Path $ToolchainBin)) {
    throw "No existe runtime\toolchain\bin. Coloca ahi los ejecutables arm-none-eabi-* antes de empaquetar."
}

$RequiredTools = @(
    "arm-none-eabi-as.exe",
    "arm-none-eabi-ld.exe",
    "arm-none-eabi-objcopy.exe",
    "arm-none-eabi-objdump.exe",
    "arm-none-eabi-nm.exe"
)

foreach ($Tool in $RequiredTools) {
    if (-not (Test-Path (Join-Path $ToolchainBin $Tool))) {
        throw "Falta $Tool en runtime\toolchain\bin."
    }
}

Push-Location $ProjectRoot
try {
    python -m PyInstaller --clean --noconfirm $SpecPath

    if (Test-Path $FinalRoot) {
        Remove-Item $FinalRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $FinalRoot | Out-Null

    Copy-Item -Path (Join-Path $PyInstallerDist "*") -Destination $FinalRoot -Recurse

    New-Item -ItemType Directory -Path (Join-Path $FinalRoot "runtime\toolchain") -Force | Out-Null
    Copy-Item -Path $ToolchainBin -Destination (Join-Path $FinalRoot "runtime\toolchain") -Recurse

    Copy-Item -Path (Join-Path $ProjectRoot "examples") -Destination (Join-Path $FinalRoot "examples") -Recurse
    Copy-Item -Path (Join-Path $ProjectRoot "packaging\README_ENTREGA.txt") -Destination (Join-Path $FinalRoot "README_ENTREGA.txt")

    if (Test-Path $FinalZip) {
        Remove-Item $FinalZip -Force
    }
    Compress-Archive -Path (Join-Path $FinalRoot "*") -DestinationPath $FinalZip

    Write-Host "Entregable creado:"
    Write-Host "  $FinalRoot"
    Write-Host "  $FinalZip"
    Write-Host ""
    Write-Host "Prueba recomendada:"
    Write-Host "  $FinalRoot\sim.exe doctor"
    Write-Host "  $FinalRoot\sim.exe check examples\exercises"
}
finally {
    Pop-Location
}
