## powershell

1. Install all packages and restart terminal
2. Setup oh-my-posh
Insert into `$PROFILE`:
```ps1
New-Item -Path $PROFILE -Type File -Force
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/powerlevel10k_classic.omp.json" | Invoke-Expression
```
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
`install-Module -Name PSReadLine -SkipPublisherCheck -Force`
5. Misc
- `Set-Alias -Name gdu -Value gdu_windows_amd64.exe`

## Other
- `setx NODE_OPTIONS "--openssl-legacy-provider"` - fix npm ssl error