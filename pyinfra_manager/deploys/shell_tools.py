import re

from pyinfra.operations import apt, server
from pyinfra.facts import apt as facts_apt, deb
from pyinfra import host

from deploys.shell_tools_vars import tools_vars
from inventory_types import InstanceComplexity


def is_source_added(source_url_regex: str) -> bool:
    source_urls = [src["url"] for src in host.get_fact(facts_apt.AptSources)]
    return any([re.match(source_url_regex, url) for url in source_urls])


def are_all_packages_installed(packages: list[str]) -> bool:
    installed_packages = host.reload_fact(deb.DebPackages)
    with open("packages.txt", "w") as f:
        f.write("\n".join(packages))
    with open("installed_packages.txt", "w") as f:
        f.write("\n".join(installed_packages))

    return all([installed_package in packages for installed_package in installed_packages])


def deploy_shell_tools() -> None:
    instance_complexity = InstanceComplexity[host.data.instance_complexity]
    packages = tools_vars.PackagesFromUbuntuNormal + tools_vars.PackagesFromReposNormal \
        if instance_complexity == InstanceComplexity.Normal \
        else (tools_vars.PackagesFromUbuntuNormal
              + tools_vars.PackagesFromReposNormal
              + tools_vars.PackagesFromUbuntuExtended
              + tools_vars.PackagesFromReposExtended
              )

    if "gh" in packages and not is_source_added(r".*cli\.github\.com.*"):
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

    if "broot" in packages and not is_source_added(r".*packages\.azlux\.fr.*"):
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

    if not are_all_packages_installed(packages):
        apt.update(_sudo=True)
        apt.packages(packages=packages, _sudo=True)
