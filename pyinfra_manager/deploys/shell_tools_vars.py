from dataclasses import dataclass


# region dataclasses
@dataclass
class ToolsVars:
    PackagesFromUbuntuNormal: list[str]
    PackagesFromUbuntuExtended: list[str]
    PackagesFromReposNormal: list[str]
    PackagesFromReposExtended: list[str]


# endregion

tools_vars = ToolsVars(
    PackagesFromUbuntuNormal=[
        "tree",
        "mc",
        "neofetch",
        "ncdu",
        "micro",
        "net-tools",
        "silversearcher-ag",
    ],
    PackagesFromUbuntuExtended=[
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
