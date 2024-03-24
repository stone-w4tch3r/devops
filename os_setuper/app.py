from abc import abstractmethod
from dataclasses import dataclass

from pyinfra import host
from pyinfra.facts import server as server_facts
from pyinfra.operations import apt, dnf, snap, server

from common import URL, OS
from units import _IUnit


# region INTERNAL

class _IInstallMethod:

    @property
    @abstractmethod
    def os(self) -> list[OS]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# endregion


# region PUBLIC

@dataclass(frozen=True)
class AptRepo:
    Key: URL
    RepoSourceStr: str
    """apt source string, e.g. `deb https://download.virtualbox.org/virtualbox/debian bionic contrib`"""


@dataclass(frozen=True)
class AptPpa:
    PpaStr: str
    """ppa formatted string, e.g. `ppa:mozillateam/ppa`"""


@dataclass(frozen=True)
class Apt(_IInstallMethod):
    PackageName: str
    Version: str | None = None
    RepoOrPpa: AptRepo | AptPpa | None = None

    @property
    def os(self) -> list[OS]: return [OS.ubuntu, OS.debian]

    @property
    def name(self) -> str: return self.PackageName


@dataclass(frozen=True)
class Dnf(_IInstallMethod):
    PackageName: str
    Version: str | None = None

    @property
    def os(self) -> list[OS]: return [OS.fedora]

    @property
    def name(self) -> str: return self.PackageName


@dataclass(frozen=True)
class Snap(_IInstallMethod):
    PackageName: str
    Version: str | None = None

    @property
    def os(self) -> list[OS]: return [OS.ubuntu, OS.debian, OS.fedora]

    @property
    def name(self) -> str: return self.PackageName


@dataclass(frozen=True)
class App(_IUnit):
    Installation: _IInstallMethod | str

    @property
    def name(self) -> str: return self.Installation.name


# endregion


def handle(apps: list[App]):
    apt_packages = [app.Installation for app in apps if isinstance(app.Installation, Apt)]
    dnf_packages = [app.Installation for app in apps if isinstance(app.Installation, Dnf)]
    snap_packages = [app.Installation for app in apps if isinstance(app.Installation, Snap)]
    str_packages = [app.Installation for app in apps if isinstance(app.Installation, str)]

    distro: OS
    match host.get_fact(server_facts.LinuxDistribution)['name']:
        case 'Ubuntu':
            distro = OS.ubuntu
        case 'Debian':
            distro = OS.debian
        case 'Fedora':
            distro = OS.fedora
        case _:
            raise Exception('Unsupported OS')

    # todo: improve this check
    assert all([distro in package.os for package in apt_packages + dnf_packages + snap_packages]), 'OS mismatch'

    for ppa in [package.RepoOrPpa.PpaStr for package in apt_packages if isinstance(package.RepoOrPpa, AptPpa)]:
        # todo: apt.ppa is not idempotent, check if ppa is already added
        apt.ppa(src=ppa, _sudo=True)
        apt.update()
    for key, repo in [(package.RepoOrPpa.Key.url_str, package.RepoOrPpa.RepoSourceStr) for package in apt_packages if
                      isinstance(package.RepoOrPpa, AptRepo)]:
        apt.key(key=key, _sudo=True)
        apt.repo(repo=repo, _sudo=True)
        apt.update()
    apt.packages(
        packages=[apt_package.PackageName for apt_package in apt_packages],
        cache_time=86400,
        update=True,
        _sudo=True
    )

    dnf.packages(
        packages=[dnf_package.PackageName for dnf_package in dnf_packages],
        _sudo=True
        # update=True,
    )

    snap.package(
        packages=[snap_package.PackageName for snap_package in snap_packages],
        _sudo=True
    )

    server.packages(
        packages=str_packages,
        _sudo=True
    )
