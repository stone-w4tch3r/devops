## powershell

1. Install all packages and restart terminal
2. Create `$PROFILE`: `New-Item -Path $PROFILE -Type File -Force`
3. Fonts:
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
4. Plugins:
`install-Module PSReadLine -SkipPublisherCheck -Force`
`Install-Module posh-git -Force`
5. Misc
- `Set-Alias -Name gdu -Value gdu_windows_amd64.exe`
6. Final `$PROFILE`:
```ps1
oh-my-posh init pwsh | Invoke-Expression
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/powerlevel10k_classic.omp.json" | Invoke-Expression

# PSReadLine
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -EditMode Windows
#Set-PSReadLineOption -PredictionViewStyle ListView
#Set-PSReadLineOption -HistorySearchCursorMovesToEnd


Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
Set-PSReadLineKeyHandler -Key Ctrl+RightArrow -Function AcceptNextSuggestionWord
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
Set-PSReadLineKeyHandler -Key Ctrl+Shift+z -Function Redo

# modules import
#Import-Module PSReadLine #?

# Aliases
Set-Alias -Name gdu -Value gdu_windows_amd64.exe
```

## Other
- `setx NODE_OPTIONS "--openssl-legacy-provider"` - fix npm ssl error