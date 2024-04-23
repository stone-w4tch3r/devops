## powershell

0. Manual activate: `irm https://massgrave.dev/get | iex`
1. Install packages and restart terminal `cat packages.json | ConvertFrom-Json | foreach { winget install $_ }`
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
1. Plugins:
`install-Module PSReadLine -SkipPublisherCheck -Force`
1. Misc
- `Set-Alias -Name gdu -Value gdu_windows_amd64.exe`
1. Final `$PROFILE`:
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