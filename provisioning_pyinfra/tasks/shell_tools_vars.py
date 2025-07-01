from dataclasses import dataclass
from enum import Enum


# region dataclasses
class ToolsComplexity(Enum):
    Normal = 0
    Extended = 1


@dataclass
class ToolsVars:
    PackagesFromAptNormal: list[str]
    PackagesFromAptExtended: list[str]
    PackagesFromReposNormal: list[str]
    PackagesFromReposExtended: list[str]


# endregion

tools_vars = ToolsVars(
    PackagesFromAptNormal=[
        "tree",
        "mc",
        "neofetch",
        "ncdu",
        "micro",
        "wl-clipboard",  # for micro clipboard integration
        "net-tools",
        "silversearcher-ag",
    ],
    PackagesFromAptExtended=[
        "python3-venv",
        "python3-pip",
    ],
    PackagesFromReposNormal=[
        "broot",
    ],
    PackagesFromReposExtended=[
        "gh",
    ],
)
