from abc import abstractmethod
from dataclasses import dataclass

from pyinfra.operations import apt

from common import URL, OS
from units import _IUnit


# region INTERNAL

class _IInstallConfig:

    @property
    @abstractmethod
    def os(self) -> list[OS]:
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
    Ppa: str
    """ppa formatted string, e.g. `ppa:mozillateam/ppa`"""


@dataclass(frozen=True)
class Apt(_IInstallConfig):
    Name: str
    Version: str | None = None
    RepoOrPpa: AptRepo | AptPpa | None = None

    @property
    def os(self) -> list[OS]: return [OS.ubuntu, OS.debian]


@dataclass(frozen=True)
class Brew(_IInstallConfig):
    Name: str
    Version: str | None = None

    @property
    def os(self) -> list[OS]: return [OS.osx]


@dataclass(frozen=True)
class App(_IUnit):
    Name: str
    Source: _IInstallConfig | str

    @property
    def name(self) -> str: return self.Name


# endregion


def handle(apps: list[App]):
    apt_packages = [app.Source for app in apps if isinstance(app.Source, Apt)]
    brew_packages = [app.Source for app in apps if isinstance(app.Source, Brew)]
    str_sources = [app.Source for app in apps if isinstance(app.Source, str)]

    for ppa in [package.RepoOrPpa for package in apt_packages if isinstance(package.RepoOrPpa, AptPpa)]:
        # todo: apt.ppa is not idempotent, check if ppa is already added
        apt.ppa(src=ppa, _sudo=True)
    for key in [package.RepoOrPpa.Key for package in apt_packages if isinstance(package.RepoOrPpa, AptRepo)]:
        apt.key(key=key, _sudo=True)
    for repo in [package.RepoOrPpa.RepoSourceStr for package in apt_packages if isinstance(package.RepoOrPpa, AptRepo)]:
        apt.repo(repo=repo, _sudo=True)
    apt.packages(
        packages=[apt_package.Name for apt_package in apt_packages],
        cache_time=86400,
        update=True,
        _sudo=True
    )
