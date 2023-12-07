from dataclasses import dataclass
from enum import Enum


# region dataclasses

class ZshComplexity(Enum):
    Normal = 0
    Extended = 1


@dataclass
class ShellDeployVars:
    Packages: list[str]
    MiscLinesAtEnd: list[str]
    ZshPluginsNormal: list[str]
    ZshPluginsExtended: list[str]
    FontsLinks: list[str]
    DebianPlugins: list[str]
    UbuntuPlugins: list[str]


# endregion


zsh_vars = ShellDeployVars(
    Packages=[
        "git",
        "zsh",
        "fzf",  # for zsh-interactive-cd
        "python3-pygments",  # for ccat/cless
        "zsh-syntax-highlighting",
        "zsh-autosuggestions",
        "thefuck",  # say 'fuck' and the error is fixed!
    ],
    MiscLinesAtEnd=[
        'setopt rmstarsilent',  # disable zsh's prompts for rm
        'eval $(thefuck -a)',
        '# To customize prompt, run "p10k configure" or edit ~/.p10k.zsh.',
        '[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh',
        '# FOR SYNTAX-HIGHLIGHTING TO WORK, THIS LINE MUST LAST',
        'source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh'
    ],
    ZshPluginsNormal=[
        "git",
        "ag",  # search
        "colored-man-pages",
        "colorize",
        "command-not-found",
        "docker",
        "docker-compose",
        "npm",
        "pip",
        "extract",  # archives
        "safe-paste",  # prevents pasted code from running
        "sudo",  # esc-esc
        "ufw",
        "zsh-interactive-cd",
    ],
    ZshPluginsExtended=[
        "dotnet",
        "adb",
        "ansible",
        "chucknorris",
        "emoji",  # get emoji as $emoji[name]
        "gh",
        "gitignore",
        "multipass",
    ],
    FontsLinks=[
        "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Regular.ttf",
        "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold.ttf",
        "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Italic.ttf",
        "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold%20Italic.ttf",
    ],
    DebianPlugins=[
        "debian",
    ],
    UbuntuPlugins=[
        "ubuntu",
    ],
)
