from dataclasses import dataclass
from enum import Enum


# region dataclasses
class AliasesComplexity(Enum):
    Minimal = -1
    Normal = 0
    Extended = 1


@dataclass
class AliasesVars:
    AliasesMinimal: list[str]
    AliasesNormal: list[str]
    AliasesExtended: list[str]


# endregion

aliases_vars = AliasesVars(
    # noqa: W605
    AliasesMinimal=[
        'alias git_cp="echo -n commit message:  && read -r message && echo \$message | git add . && git commit -m \$message && git push"',
    ],
    AliasesNormal=[
        'alias f=fuck',
        "alias cat=ccat",
        "alias less=cless",
    ],
    AliasesExtended=[
        "alias gitignore=gi",
        'alias codium="NODE_OPTIONS=\"\" codium --enable-features=UseOzonePlatform --ozone-platform=wayland"',  # wayland support
        'alias multipass_recreate-primary="~/Projects/devops/scripts/multipass_recreate_primary.py"',
        'alias \?\?="gh copilot suggest -t shell"',
        'alias \?!="gh copilot explain"',
    ]
)
