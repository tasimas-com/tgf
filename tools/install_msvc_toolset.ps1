[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^14\.\d+$')]
    [string]$ToolsetVersion,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ComponentId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ChannelId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [uri]$BootstrapperUri
)

$ErrorActionPreference = "Stop"

$programFilesX86 = [Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)
if ([string]::IsNullOrWhiteSpace($programFilesX86)) {
    throw "Windows did not provide the ProgramFilesX86 directory."
}

$installerRoot = Join-Path $programFilesX86 "Microsoft Visual Studio\Installer"
$vswhere = Join-Path $installerRoot "vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw "vswhere.exe was not found at '$vswhere'."
}

$vsPath = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($vsPath)) {
    throw "No Visual Studio installation with the x64/x86 MSVC tools was found."
}

$installationVersion = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion
$productId = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property productId
$toolsetRoot = Join-Path $vsPath "VC\Tools\MSVC"

Write-Host "Selected Visual Studio instance: $vsPath"
Write-Host "Visual Studio version: $installationVersion"
Write-Host "Visual Studio product: $productId"
Write-Host "Requested channel: $ChannelId"
Write-Host "MSVC toolsets before provisioning:"
Get-ChildItem -LiteralPath $toolsetRoot -Directory -ErrorAction Stop |
    Sort-Object Name |
    ForEach-Object { Write-Host "  $($_.Name)" }

$toolset = Get-ChildItem -LiteralPath $toolsetRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "$ToolsetVersion.*" } |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $toolset) {
    $bootstrapper = Join-Path $env:RUNNER_TEMP "vs_enterprise_18.11.4_ltsc.exe"
    Invoke-WebRequest -Uri $BootstrapperUri -OutFile $bootstrapper

    $signature = Get-AuthenticodeSignature -FilePath $bootstrapper
    if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notmatch "Microsoft Corporation") {
        throw "Downloaded Visual Studio bootstrapper does not have a valid Microsoft Authenticode signature."
    }

    # A single quoted command line is required because the installation path contains spaces.
    # The fixed 18.11 LTSC bootstrapper must modify the matching LTSC Visual Studio instance.
    $installerArguments = 'modify --installPath "{0}" --channelId "{1}" --add "{2}" --quiet --norestart --wait' -f $vsPath, $ChannelId, $ComponentId
    Write-Host "Visual Studio bootstrapper command: $installerArguments"

    $installerProcess = Start-Process -FilePath $bootstrapper -ArgumentList $installerArguments -Wait -PassThru
    $installExitCode = $installerProcess.ExitCode
    Write-Host "Visual Studio bootstrapper exit code: $installExitCode"
    if ($installExitCode -notin @(0, 3010)) {
        throw "Visual Studio bootstrapper failed to install MSVC $ToolsetVersion (exit $installExitCode)."
    }

    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $toolset = Get-ChildItem -LiteralPath $toolsetRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "$ToolsetVersion.*" } |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($toolset) { break }
        Start-Sleep -Seconds 5
    }
}

if (-not $toolset) {
    Write-Host "MSVC toolsets after provisioning:"
    Get-ChildItem -LiteralPath $toolsetRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name |
        ForEach-Object { Write-Host "  $($_.Name)" }

    $logRoots = @(
        $env:TEMP,
        (Join-Path $env:ProgramData "Microsoft\VisualStudio\Setup\Logs")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Container }

    foreach ($logRoot in $logRoots) {
        $recentLogs = Get-ChildItem -LiteralPath $logRoot -Filter "dd_*.log" -File -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 3
        foreach ($log in $recentLogs) {
            Write-Host "===== Visual Studio installer log: $($log.FullName) ====="
            Get-Content -LiteralPath $log.FullName -Tail 100
        }
    }

    throw "MSVC $ToolsetVersion was not installed; refusing to fall back to another compiler."
}

Write-Host "Selected MSVC toolset directory: $($toolset.FullName)"
