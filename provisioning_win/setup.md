## install winget

Simple:

```ps1
$progressPreference = 'silentlyContinue'
Invoke-WebRequest -Uri https://aka.ms/getwinget -OutFile Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
Add-AppxPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
Remove-Item Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
```

Complex:

```ps1
cd ~/Downloads/

$progressPreference = 'silentlyContinue'

# dependencies
Invoke-WebRequest -Uri https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx -OutFile Microsoft.VCLibs.x64.14.00.Desktop.appx
Invoke-WebRequest -Uri https://github.com/microsoft/microsoft-ui-xaml/releases/download/v2.8.6/Microsoft.UI.Xaml.2.8.x64.appx -OutFile Microsoft.UI.Xaml.2.8.x64.appx

# check latest version manually
Invoke-WebRequest -Uri https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle -OutFile Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle


Add-AppxPackage Microsoft.VCLibs.x64.14.00.Desktop.appx
Add-AppxPackage Microsoft.UI.Xaml.2.8.x64.appx
Add-AppxPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle

rm Microsoft.VCLibs.x64.14.00.Desktop.appx
rm Microsoft.UI.Xaml.2.8.x64.appx
rm Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
```

## powershell

0. Manual activate: `irm https://massgrave.dev/get | iex`
1. Install packages and restart terminal `cat packages.json | ConvertFrom-Json | foreach { winget install --source winget $_ }`
2. `set-executionpolicy remotesigned`
3. Create `$PROFILE`: `New-Item -Path $PROFILE -Type File -Force`
4. Fonts:
`oh-my-posh font install Meslo`
In MS Terminal `settings.json` ensure:

```json
{
    "profiles":
    {
        "defaults":
        {
            "font":
            {
                "face": "MesloLGM Nerd Font"
            }
        }
    }
}
```

5. Plugins:
`Install-Module PSReadLine -SkipPublisherCheck -Force`
`Install-Module Microsoft.WinGet.Client -SkipPublisherCheck -Force` (powershell wrapper)
6. `python3` symlinc:
`$venv=((get-command python).source | Get-ItemProperty).DirectoryName;New-Item -Path $venv -Name "python3.exe" -Value "$venv\python.exe" -ItemType SymbolicLink`

## Final `$PROFILE`

```ps1
oh-my-posh init pwsh | Invoke-Expression
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/powerlevel10k_classic.omp.json" | Invoke-Expression

# PSReadLine
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -EditMode Windows
#Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineOption -HistorySearchCursorMovesToEnd


Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
Set-PSReadLineKeyHandler -Key Ctrl+Alt+RightArrow -Function AcceptNextSuggestionWord
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
Set-PSReadLineKeyHandler -Key Ctrl+Shift+z -Function Redo

# modules import
#Import-Module PSReadLine #?

# Aliases
# Set-Alias -Name gdu -Value gdu_windows_amd64.exe # may be needed
```

## Other

- fix npm ssl error: `setx NODE_OPTIONS "--openssl-legacy-provider"`
- add .caps-layout.ahk and symlink it to startup folder
- fix VBox Hyper-V conflict:

    ```ps1
    Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Hypervisor

    $registryPath1 = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard"
    if (!(Test-Path $registryPath1)) {
        New-Item -Path $registryPath1 -Force | Out-Null
    }

    Set-ItemProperty -Path $registryPath1 -Name "LsaCfgFlags" -Value 0
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "LsaCfgFlags" -Value 0
    ```

    And disable Core Isolation: Defender > Device Security > Core Isolation

## Take $PATH from another user

```ps1
$currentUsername = "USERNAME_HERE"
$targetUsername = "TARGET_USERNAME_HERE"

$sid = (New-Object System.Security.Principal.NTAccount($targetUsername)).Translate([System.Security.Principal.SecurityIdentifier]).Value
$UserHive = Get-ChildItem Registry::HKEY_USERS\ | Where-Object { $_.Name -eq "HKEY_USERS\$sid" }
if ($UserHive) {
    $userPath = (Get-ItemProperty -Path "$($UserHive.PSPath)\Environment" -Name PATH -ErrorAction SilentlyContinue).Path

    if ($userPath) {
        Write-Output '$PATH was copied from another user, see $PROFILE'
    } else {
        Write-Output "No custom PATH found for user ${targetUsername}"
    }
} else {
    Write-Output "User profile for ${targetUsername} not found or not loaded"
}

# Combine the paths, removing duplicates TODO fix
# $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
# $newPath = ($currentPath.Split(';') + $userPath.Split(';') | Select-Object -Unique) -join ';'

# fix strange bug when PATH env var contains wrong pathes
$newPath = $userPath -replace $currentUsername, $targetUsername

# Set the new PATH for the current session
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + $newPath

# cd to targetUsername's home dir
$me = "C:\Users\${targetUsername}\"
cd $me
```
