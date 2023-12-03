import os

from pyinfra import host
from pyinfra.facts import files as facts_files
from pyinfra.facts import server as facts_server
from pyinfra.operations import apt, server, files, git, python

from deploys.zsh_vars import zsh_vars
from inventory_types import InstanceComplexity


def is_ohmyzsh_installed_initially(home_path: str) -> bool:
    return host.get_fact(facts_files.Directory, f"{home_path}/.oh-my-zsh")


def assert_zsh_correctly_installed_dynamic(home_path: str) -> None:
    assert host.reload_fact(facts_files.File, f"{home_path}/.zshrc")
    assert host.reload_fact(facts_files.Directory, f"{home_path}/.oh-my-zsh")


def deploy_zsh() -> None:
    instance_complexity = InstanceComplexity[host.data.instance_complexity]
    packages = zsh_vars.Packages
    home_path = f"/home/{host.data.server_user}"
    fonts_links = zsh_vars.FontsLinks
    current_dir = os.path.dirname(os.path.abspath(__file__))
    p10k_to_put = f"{current_dir}/files/p10k_normal.zsh" \
        if instance_complexity == InstanceComplexity.Normal \
        else f"{current_dir}/files/p10k_extended.zsh"
    misc_lines_block_content = zsh_vars.MiscLinesAtEnd
    plugins_str = " ".join(zsh_vars.ZshPluginsNormal) \
        if instance_complexity == InstanceComplexity.Normal \
        else " ".join(zsh_vars.ZshPluginsNormal + zsh_vars.ZshPluginsExtended)
    if host.get_fact(facts_server.LinuxName) == "debian":
        plugins_str += " " + " ".join(zsh_vars.DebianPlugins)
    if host.get_fact(facts_server.LinuxName) == "ubuntu":
        plugins_str += " " + " ".join(zsh_vars.UbuntuPlugins)

    apt.update(cache_time=86400, _sudo=True)
    apt.packages(packages=packages, _sudo=True)

    server.user(user=host.data.server_user, shell="/usr/bin/zsh", _sudo=True)

    if not is_ohmyzsh_installed_initially(home_path):
        server.shell(
            commands='sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended',
            _sudo_user=host.data.server_user,
            _use_sudo_login=True,
            _sudo=True,
        )

    python.call(
        name="Assert zsh correctly installed",
        function=lambda: assert_zsh_correctly_installed_dynamic(home_path)
    )

    if host.get_fact(facts_server.LinuxGui) and host.data.get("supress_linux_gui_warning") is not True:
        raise Exception("Linux GUI detected. Manually re-login to continue, than run again with '--data supress_linux_gui_warning=True'")

    git.repo(src="https://github.com/romkatv/powerlevel10k", dest=f"{home_path}/.oh-my-zsh/custom/themes/powerlevel10k", pull=False, _sudo=True)
    files.put(src=p10k_to_put, dest=f"{home_path}/.p10k.zsh", mode="0644", _sudo=True)

    files.line(path="/etc/environment", line="zic_case_insensitive=true", _sudo=True)

    files.line(path=f"{home_path}/.zshrc", replace=f"plugins=({plugins_str})", line="^plugins=.*", _sudo=True)
    files.line(path=f"{home_path}/.zshrc", replace="ZSH_THEME=\"powerlevel10k/powerlevel10k\"", line="^ZSH_THEME=.*", _sudo=True)

    python.call(
        name="Add misc lines to end of .zshrc",
        function=lambda: files.block(
            path=f"{home_path}/.zshrc",
            content=misc_lines_block_content,
            marker="#### {mark} MISC LINES BLOCK ####",
            try_prevent_shell_expansion=True,
            _sudo=True
        )
    )

    if instance_complexity == InstanceComplexity.Extended:
        files.directory(path="/usr/share/fonts/truetype/", present=True, _sudo=True)
        for link in fonts_links:
            filename = link.split("/")[-1].replace("%20", " ")
            files.download(src=link, dest=f"/usr/share/fonts/truetype/{filename}", mode="0644", _sudo=True)
