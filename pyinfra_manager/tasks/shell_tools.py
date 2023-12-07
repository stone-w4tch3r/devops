import re
from pyinfra.operations import apt, server, python
from pyinfra.facts import apt as facts_apt, deb
from pyinfra import host
from tasks.shell_tools_vars import tools_vars, ToolsComplexity


def _is_source_added_initially(source_url_regex: str) -> bool:
    source_urls = [src["url"] for src in host.get_fact(facts_apt.AptSources)]
    return any([re.match(source_url_regex, url) for url in source_urls])


def _are_all_packages_installed_initially(packages: list[str]) -> bool:
    installed_packages = host.get_fact(deb.DebPackages)
    return all([package in installed_packages for package in packages])


def _ensure_micro_configuration_dynamically() -> None:
    is_micro_installed = host.reload_fact(deb.DebPackage, "micro")
    assert is_micro_installed, "micro is not installed"

    _, stdout, _ = host.run_shell_command("update-alternatives --list editor")
    if "micro" not in ' '.join(stdout):
        server.shell(
            name="Shell: install micro into update-alternatives as default editor",
            commands="sudo update-alternatives --install /usr/bin/editor editor /usr/bin/micro 100",  # 100 - high priority
            _sudo=True
        )
        return

    server.shell(
        name="Shell: Set micro as default editor",
        commands="sudo update-alternatives --set editor /usr/bin/micro",
        _sudo=True
    )


def deploy_shell_tools() -> None:
    tools_complexity = ToolsComplexity[host.data.tools_complexity]
    packages: list[str] = []
    if tools_complexity == ToolsComplexity.Normal:
        packages = tools_vars.PackagesFromAptNormal + tools_vars.PackagesFromReposNormal
    if tools_complexity == ToolsComplexity.Extended:
        packages = (tools_vars.PackagesFromAptNormal
                    + tools_vars.PackagesFromReposNormal
                    + tools_vars.PackagesFromAptExtended
                    + tools_vars.PackagesFromReposExtended
                    )

    if "gh" in packages and not _is_source_added_initially(r".*cli\.github\.com.*"):
        server.shell(
            name="Shell: Add gh source to apt",
            commands=
            """
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
            && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
            && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
                https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            """,
            _sudo=True
        )

    if "broot" in packages and not _is_source_added_initially(r".*packages\.azlux\.fr.*"):
        server.shell(
            name="Shell: Add broot source to apt",
            commands=
            """
            echo "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] http://packages.azlux.fr/debian/ stable main" \
                | sudo tee /etc/apt/sources.list.d/azlux.list
            sudo wget -O /usr/share/keyrings/azlux-archive-keyring.gpg  https://azlux.fr/repo.gpg
            """,
            _sudo=True
        )

    if not _are_all_packages_installed_initially(packages):
        apt.update(_sudo=True)
        apt.packages(packages=packages, _sudo=True)

    is_micro_installed = host.get_fact(deb.DebPackage, "micro")
    if "micro" in packages or is_micro_installed:
        python.call(
            name="Ensure micro as default editor",
            function=lambda: _ensure_micro_configuration_dynamically()
        )
