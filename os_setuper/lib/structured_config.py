from dataclasses import dataclass
from enum import Enum, auto

from pyinfra import host, logger
from pyinfra.api import operation, StringCommand
from pyinfra.facts import files as files_fact


class ConfigType(Enum):
    json = auto()
    yaml = auto()


@dataclass
class ArrayItem:
    Value: str


@dataclass(frozen=True)
class EntryState:
    Property: str
    Value: str | ArrayItem
    Present: bool = True
    Overwrite: bool = True


@operation
def modify_config(
    entries: list[EntryState] | EntryState,
    config_type: ConfigType,
    path: str,
    backup: bool = True,
):
    if not isinstance(entries, list):
        entries = [entries]

    match host.get_fact(files_fact.File, path=path):
        case None:
            logger.error(f"Config file {path} not found")
            return
        case False:
            logger.error(f"Config file {path} is not a file")
            return
        case {"size": size} if size > (1024 * 1024):  # 1MB
            logger.error(f"Config file {path} is too large to process: {size}")
            return

    if backup:
        yield StringCommand(f"cp {path} {path}.bak")

    # todo: implement
