from pyinfra import host
from pyinfra.operations import files, python
from tasks.shell_aliases_vars import aliases_vars, AliasesComplexity


def _find_target_file_and_write_aliases(aliases_block_content: str, home_path: str) -> None:
    target_file = f"{home_path}/.bashrc"
    if host.reload_fact(files.File, f"{home_path}/.zshrc"):
        target_file = f"{home_path}/.zshrc"

    files.block(
        path=target_file,
        content=aliases_block_content,
        marker="#### {mark} ALIASES BLOCK ####",
        try_prevent_shell_expansion=True,
        _sudo=True
    )


def deploy_aliases() -> None:
    aliases_complexity = AliasesComplexity[host.data.aliases_complexity]
    home_path = f"/home/{host.data.server_user}"
    aliases_block_content = aliases_vars.AliasesMinimal
    if aliases_complexity == AliasesComplexity.Normal:
        aliases_block_content += aliases_vars.AliasesNormal
    if aliases_complexity == AliasesComplexity.Extended:
        aliases_block_content += aliases_vars.AliasesNormal + aliases_vars.AliasesExtended

    python.call(
        name="Find target file and write aliases",
        function=lambda: _find_target_file_and_write_aliases(aliases_block_content, home_path)
    )
