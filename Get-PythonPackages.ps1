# PowerShell script to manage Python packages
# Self-elevate the script if require
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
        $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
        Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
        Exit
    }
}

# Step 1: Pip freeze and uninstall all packages
$pipFreeze = pip freeze
$pipFreeze | ForEach-Object {
    pip uninstall -y $_
}

# Step 2: Install pipreqs
pip install pipreqs

# Step 3: Generate requirements.txt in the current directory
pipreqs --encoding=utf8 ./ --force

# Step 4: Download packages from requirements.txt to the Packages directory
$requirements = Get-Content -Path ./requirements.txt
$requirements | ForEach-Object {
    pip download $_ -d ./Packages
}
