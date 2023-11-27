from dataclasses import dataclass


# region dataclasses
@dataclass
class AliasesVars:
    AliasesNormal: list[str]
    AliasesExtended: list[str]


# endregion

aliases_vars = AliasesVars(
    # noqa: W605
    AliasesNormal=[
        'f=fuck',
        "alias cat=ccat",
        "alias less=cless",
        'alias git_cp="echo -n commit message:  && read -r message && echo \$message | git add . && git commit -m \$message && git push"',
    ],
    AliasesExtended=[
        "alias gitignore=gi",
        'alias codium="NODE_OPTIONS=\"\" codium --enable-features=UseOzonePlatform --ozone-platform=wayland"',  # wayland support
        'alias multipass_recreate-primary="~/Projects/devops/scripts/multipass/recreate_multipass_primary.py"',
        'alias \?\?="gh copilot suggest -t shell"',
        'alias \?!="gh copilot explain"',
    ]
)
