from pyinfra import host
from pyinfra.operations import files, python
from pyinfra.facts import server as facts_server
from deploys.shell_aliases_vars import aliases_vars
from inventory_types import InstanceComplexity


def _find_target_file_and_write_aliases(aliases_block_content: str, home_path: str) -> None:
    target_file = f"{home_path}/.bashrc"
    if host.reload_fact(files.File, f"{home_path}/.zshrc"):
        target_file = f"{home_path}/.zshrc"

    files.block(
        path=target_file,
        content=aliases_block_content,
        marker="#### {mark} ALIASES BLOCK ####",
        try_prevent_shell_expansion=True,
    )


def deploy_aliases() -> None:
    instance_complexity = InstanceComplexity[host.data.instance_complexity]
    home_path = f"/home/{host.get_fact(facts_server.User)}"
    aliases_block_content = aliases_vars.AliasesMinimal
    if instance_complexity == InstanceComplexity.Normal:
        aliases_block_content += aliases_vars.AliasesNormal
    if instance_complexity == InstanceComplexity.Extended:
        aliases_block_content += aliases_vars.AliasesNormal + aliases_vars.AliasesExtended

    python.call(
        name="Find target file and write aliases",
        function=lambda: _find_target_file_and_write_aliases(aliases_block_content, home_path)
    )
