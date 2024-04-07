import configparser
import copy
import datetime
import json
import plistlib
from enum import Enum, auto
from io import StringIO
from typing import Callable

import xmltodict
from pyinfra import host, logger
from pyinfra.api import operation, OperationError, OperationValueError
from pyinfra.facts import files as files_fact, server
from pyinfra.operations import files


def _deserialize(content: str, deserializer: Callable[[str], dict]) -> dict:
    try:
        return deserializer(content)
    except Exception as e:
        raise OperationError(f"Error while deserializing: {e}")


def _serialize(config: dict, serializer: Callable[[dict], str]) -> str:
    try:
        return serializer(config)
    except Exception as e:
        raise OperationError(f"Error while serializing: {e}")


class ConfigType(Enum):
    JSON = auto()
    XML = auto()
    INI = auto()
    PLIST = auto()
    # TOML = auto() # todo: what is minimal python version?
    CUSTOM = auto()


@operation()
def modify_config(
    path: str,
    modify_action: Callable[[dict], dict],
    config_type: ConfigType = ConfigType.JSON,
    backup: bool = False,
    custom_deserializer: Callable[[str], dict] = None,
    custom_serializer: Callable[[dict], str] = None,
    max_file_size_mb: int = 2,
):
    """
    Modify a structured config file on the remote host.
    Config file would be loaded from the remote host, modified, and then uploaded back to the remote host.

    @note If the config file is too large, this operation will be slow.

    @param modify_action: A function that modifies the config passed in as a dict, and returns the modified config.
    @param config_type: The type of the config file.
    @param path: The path to the config file.
    @param backup: Whether to create a backup of the config file before modifying it.
    @param custom_deserializer: A function that deserializes the config file content to a dict. Only used if config_type is CUSTOM.
    @param custom_serializer: A function that serializes the config dict to a string. Only used if config_type is CUSTOM.
    @param max_file_size_mb: The maximum allowed size of the config file in MB. If the file is larger than this, an error will be raised.
    """
    # todo: exceptions or log errors?
    # validation
    if config_type == ConfigType.CUSTOM and (custom_deserializer is None or custom_serializer is None):
        raise OperationValueError("custom_deserializer and custom_serializer must be provided if config_type is CUSTOM")
    match host.get_fact(files_fact.File, path=path):
        case None:
            raise OperationValueError(f"Config file {path} not found")
        case False:
            raise OperationValueError(f"Config file {path} is not a file")
        case {"size": size_bytes} if size_bytes > max_file_size_mb * 1024 * 1024:
            raise OperationValueError(f"Config file {path} is too large to process: {size_bytes / 1024 / 1024} MB")
        case {"mode": mode_int, "user": file_owner, "group": file_group}:  # check if readable/writable
            user: str = host.get_fact(server.User)
            user_groups: list[str] = host.get_fact(server.Users)[user]["groups"]
            mode_str = str(mode_int)  # mode_int is 3-digit int e.g. 644
            owner_can_rw = mode_str[0] in "67"
            group_can_rw = mode_str[1] in "67"
            other_can_rw = mode_str[2] in "67"
            if (file_owner == user and owner_can_rw) or (file_group in user_groups and group_can_rw) or other_can_rw:
                pass
            else:
                logger.debug(f"owner_can_rw [{owner_can_rw}], group_can_rw [{group_can_rw}], other_can_rw [{other_can_rw}]")
                logger.debug(f"User [{user}], groups [{user_groups}], file owner [{file_owner}], file group [{file_group}], mode [{mode_int}]")
                raise OperationError(f"Config file {path} is not readable/writable by the current user")

    # load file
    config_str: str = host.get_fact(files_fact.FileContent, path=path)
    if config_str is None:
        raise OperationError(f"Failed to read config file {path}")

    # deserialize
    config: dict | None = None
    if not config_str.strip():  # is empty or whitespace
        config = {}
    elif config_type == ConfigType.JSON:
        config = _deserialize(config_str, json.loads)
    elif config_type == ConfigType.INI:
        def _parse_ini(content: str) -> dict:
            config_parser = configparser.ConfigParser()
            config_parser.read_string(content)
            return {section: dict(config_parser[section]) for section in config_parser.sections()}

        config = _deserialize(config_str, _parse_ini)
    elif config_type == ConfigType.XML:
        config = _deserialize(config_str, xmltodict.parse)
    elif config_type == ConfigType.PLIST:
        config = _deserialize(config_str, lambda content: plistlib.loads(content.encode("utf-8")))
    elif config_type == ConfigType.CUSTOM:
        config = _deserialize(config_str, custom_deserializer)
        if not isinstance(config, dict): raise OperationError(f"Custom deserializer must return a dict")
    if config is None:
        raise OperationError(f"Failure while deserializing config file. This is not supposed to happen. Report a bug.")

    # modify
    modified_config = modify_action(copy.deepcopy(config))

    # serialize
    modified_config_str: str | None = None
    if config_type == ConfigType.JSON:
        modified_config_str = _serialize(modified_config, lambda cfg: json.dumps(cfg, indent=4))
    elif config_type == ConfigType.INI:
        def _serialize_ini(cfg: dict) -> str:
            config_parser = configparser.ConfigParser()
            for section, section_config in cfg.items():
                config_parser[section] = section_config
            with StringIO() as f:
                config_parser.write(f)
                return f.getvalue()

        modified_config_str = _serialize(modified_config, _serialize_ini)
    elif config_type == ConfigType.XML:
        modified_config_str = _serialize(modified_config, lambda cfg: xmltodict.unparse(cfg, pretty=True))
    elif config_type == ConfigType.PLIST:
        modified_config_str = _serialize(modified_config, lambda cfg: plistlib.dumps(cfg).decode("utf-8"))
    elif config_type == ConfigType.CUSTOM:
        modified_config_str = _serialize(modified_config, custom_serializer)
        if not isinstance(modified_config_str, str): raise OperationError(f"Custom serializer must return a string")
    if modified_config_str is None:
        raise OperationError(f"Failure while serializing config file. This is not supposed to happen. Report a bug.")

    # upload
    if modified_config_str == config_str:
        host.noop(f"Config file {path} is already up-to-date")
        return
    if backup:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        yield from files.put._inner(
            src=StringIO(config_str),
            dest=f"{path}.bak_{timestamp}",
        )
    yield from files.put._inner(
        src=StringIO(modified_config_str),
        dest=path,
    )
