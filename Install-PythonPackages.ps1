# PowerShell script to install Python packages from a local 'Packages' directory
# Self-elevate the script if require
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
        $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
        Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
        Exit
    }
}

# Define the path to the 'Packages' directory and 'requirements.txt' file
$packagesDir = Join-Path -Path $PSScriptRoot -ChildPath "Packages"
$reqFile = Join-Path -Path $PSScriptRoot -ChildPath "requirements.txt"

# Check if 'requirements.txt' exists
if (-not (Test-Path -Path $reqFile)) {
    Write-Error "requirements.txt not found in the script directory."
    exit
}

# Install each package listed in 'requirements.txt' from the 'Packages' directory
Get-Content -Path $reqFile | ForEach-Object {
    $packageName = $_
    Write-Host "Installing package: $packageName"
    pip install --no-index --find-links $packagesDir $packageName
}

Write-Host "All packages have been installed."
