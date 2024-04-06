import copy
import json
from enum import Enum, auto
from io import StringIO
from typing import Callable

from pyinfra import host, logger
from pyinfra.api import operation, OperationError
from pyinfra.facts import files as files_fact
from pyinfra.operations import files


class ConfigType(Enum):
    json = auto()
    yaml = auto()


@operation()
def modify_config(
    modify_action: Callable[[dict], dict],
    config_type: ConfigType,
    path: str,
    backup: bool = True,
):
    # validation
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

    # load file
    config_str: str = host.get_fact(files_fact.FileContent, path=path)
    if config_str is None:
        raise OperationError(f"Failed to read config file {path}")

    # deserialize
    config: dict = {}
    if not config_str.strip():  # is empty or whitespace
        config = {}
    elif config_type == ConfigType.json:
        try:
            config = json.loads(config_str)
        except Exception as e:
            raise OperationError(f"Error decoding JSON file {path}: {e}")
    elif config_type == ConfigType.yaml:
        raise NotImplementedError()

    # modify
    modified_config_str = modify_action(copy.deepcopy(config))
    if modified_config_str == config:
        host.noop(f"Config file {path} is already up-to-date")
        return

    # serialize
    if config_type == ConfigType.json:
        modified_config_str = json.dumps(modified_config_str, indent=2)
    elif config_type == ConfigType.yaml:
        raise NotImplementedError()

    # upload
    if modified_config_str == config_str:
        host.noop(f"Config file {path} is already up-to-date")
        return
    if backup:
        yield from files.put._inner(
            src=StringIO(config_str),
            dest=f"{path}.bak",
        )
    yield from files.put._inner(
        src=StringIO(modified_config_str),
        dest=path,
    )
