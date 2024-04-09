import configparser
import copy
import datetime
import inspect
import json
import plistlib
import traceback
from enum import Enum
from io import StringIO
from typing import Callable, Any, TypeVar

import xmltodict
from pyinfra import host, logger
from pyinfra.api import operation, OperationError, OperationValueError, FunctionCommand
from pyinfra.facts import files as files_fact, server
from pyinfra.operations import files


class DictWrapper:
    """
    A wrapper that allows modification withing lambda.
    Python is, so to speak, a "simple and convenient" language, so some tricky workarounds are required to work with lambda functions.

    Usage:
    ```
    dct = { "cars": { "car0": "Toyota", "car1": "BMW", } }
    modified_dct = DictWrapper(dct)["cars"]["car0"].set("Mercedes")
    modified_dct = DictWrapper(dct)["cars"]["car1"].remove()
    modified_dct = DictWrapper(dct)["numbers"].set([1, 2, 3])
    modified_dct = DictWrapper(dct)["numbers"].append(4)
    ```

    Usage with chained operations:
    ```
    dct = { "cars": { "car0": "Toyota", "car1": "BMW", } }
    modified_dct = DictWrapper(dct).modify_chained([
        lambda x: x["cars"]["car0"].set("Mercedes"),
        lambda x: x["cars"]["car1"].set("Audi"),
    ])
    """
    _node: dict
    _key: str
    _root: dict

    def __init__(self, node: dict, key: str = None, root: dict = None):
        self._node = node
        self._key = key
        self._root = root

    def __getitem__(self, key: str):
        if self._root is None:
            return DictWrapper(self._node, key, self._node)
        return DictWrapper(self._node[self._key], key, self._root)

    def set(self, value: Any) -> dict:
        """
        Equal to `dct[key] = value`.
        """
        self._node[self._key] = value
        return self._root or self._node

    def append(self, value: Any) -> dict:
        """
        Equal to `dct[key].append(value)`.
        """
        self._node[self._key].append(value)
        return self._root or self._node

    def remove(self) -> dict:
        """
        Equal to `dct.pop(key)`.
        """
        self._node.pop(self._key)
        return self._root or self._node

    def modify_chained(self, list_of_operations: list[Callable[["DictWrapper"], dict]]) -> dict:
        """
        Chained dictionary modifications.

        Usage:
        ```
        dct = { "cars": { "car0": "Toyota", "car1": "BMW", } }
        modified_dct = DictWrapper(dct).modify_chained([
            lambda x: x["cars"]["car0"].set("Mercedes"),
            lambda x: x["cars"]["car1"].set("Audi"),
        ])
        ```
        """
        dct = self._root if self._root is not None else self._node
        for o in list_of_operations:
            dct = o(DictWrapper(dct))
            if not isinstance(dct, dict):
                raise OperationError(f"Chained operations must return a dictionary, got {type(dct)} from {inspect.getsource(o).lstrip()}")
        return dct

    @property
    def dct(self) -> dict:
        return self._root or self._node


class ListWrapper:
    """
    A wrapper that allows modification withing lambda.
    Python is, so to speak, a "simple and convenient" language, so some tricky workarounds are required to work with lambda functions.

    Usage:
    ```
    lst = [1, 2, 3]
    modified_lst = ListWrapper(lst).append(4)
    modified_lst = ListWrapper(lst)[0].set(5)
    modified_lst = ListWrapper(lst).remove(0)
    ```

    Usage with chained operations:
    ```
    lst = [1, 2, 3]
    modified_lst = ListWrapper(lst).modify_chained([
        lambda x: x.append(4),
        lambda x: x[0].set(5),
    ])
    """

    class _ListElementWrapper:
        def __init__(self, lst: list, index: int, root: list):
            self._lst = lst
            self._index = index
            self._root = root

        def set(self, value: Any) -> list:
            """
            Equal to `lst[index] = value`.
            """
            self._lst[self._index] = value
            return self._root

    def __init__(self, lst: list):
        self.lst = lst

    def __getitem__(self, index):
        if isinstance(index, slice):
            raise ValueError("Slicing is not supported. Use lst property to get the inner list.")
        else:
            return ListWrapper._ListElementWrapper(self.lst, index, self.lst)

    def remove(self, index: int) -> list:
        """
        Equal to `lst.pop(index)`.
        """
        self.lst.pop(index)
        return self.lst

    def append(self, value: Any) -> list:
        """
        Equal to `lst.append(value)`.
        """
        self.lst.append(value)
        return self.lst

    def modify_chained(self, list_of_operations: list[Callable[["ListWrapper"], list]]) -> list:
        """
        Chained list modifications.

        Usage:
        ```
        lst = [1, 2, 3]
        modified_lst = ListWrapper(lst).modify_chained([
            lambda x: x.append(4),
            lambda x: x[0].set(5),
        ])
        ```
        """
        lst = self.lst
        for o in list_of_operations:
            lst = o(ListWrapper(lst))
            if not isinstance(lst, list):
                raise OperationError(f"Chained operations must return a list, got {type(lst)} from {inspect.getsource(o).lstrip()}")
        return lst


_T = TypeVar("_T")


def _deserialize(content: str, deserializer: Callable[[str], _T]) -> _T:
    try:
        return deserializer(content)
    except Exception as e:
        raise OperationError(f"Error while deserializing: {repr(e)}")


def _serialize(config: _T, serializer: Callable[[_T], str]) -> str:
    try:
        return serializer(config)
    except Exception as e:
        raise OperationError(f"Error while serializing: {repr(e)}")


def _deserialize_ini(content: str) -> dict | list:
    config_parser = configparser.ConfigParser()
    config_parser.read_string(content)
    return {section: dict(config_parser[section]) for section in config_parser.sections()}


def _serialize_ini(cfg: dict | list) -> str:
    config_parser = configparser.ConfigParser()
    for section, section_config in cfg.items():
        config_parser[section] = section_config
    with StringIO() as f:
        config_parser.write(f)
        return f.getvalue()


def _validate_file_state(path: str, max_file_size_mb: int) -> None:
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


class ConfigType(Enum):
    JSON = "JSON"
    XML = "XML"
    INI = "INI"
    PLIST = "PLIST"
    # TOML = "TOML # todo: what is minimal python version?


TDeserialized = TypeVar("TDeserialized")
TSerialize = TypeVar("TSerialize")


@operation()
def modify_config_fluent(
    path: str,
    modify_action: Callable[[DictWrapper | ListWrapper | TDeserialized], dict | list],
    config_type: ConfigType | None = ConfigType.JSON,
    custom_deserializer: Callable[[str], TDeserialized] = None,
    custom_serializer: Callable[[TDeserialized], str] = None,
    backup: bool = False,
    max_file_size_mb: int = 2,
):
    """
    Modify a structured config file on the remote host.
    DictWrapper and ListWrapper are provided to allow quick in-place modifications within lambda functions.
    Config file would be loaded from the remote host, modified, and then uploaded back to the remote host.

    @note If the config file is too large, this operation will be slow.
    @note If config_type is provided, custom_deserializer and custom_serializer are ignored.

    @param path: The path to the config file.
    @param modify_action: A function that modifies config and returns modified value.
    @param config_type: The type of the config file.
    @param custom_deserializer: A function that deserializes the config file content.
    @param custom_serializer: A function that serializes the config to a string.
    @param backup: Whether to create a backup of the config file before modifying it.
    @param max_file_size_mb: Max allowed size of the config file in MB.

    Usage:
    ```
    structured_config.modify_config_fluent(
        path="/file.json",
        modify_action=lambda cfg: cfg["cars"]["car0"].set("Mercedes"),
    )
    ```

    Usage with chained operations:
    ```
    structured_config.modify_config_fluent(
        path="/file.json",
        modify_action=lambda cfg: cfg.modify_chained([
            lambda x: x["cars"]["car0"].set("Mercedes"),
            lambda x: x["cars"]["car1"].set("Audi"),
        ])
    )
    ```

    Usage with custom deserializer and serializer:
    ```
    import yaml
    structured_config.modify_config_fluent(
        path="/file.yaml",
        modify_action=lambda cfg: cfg["cars"]["car0"].set("Mercedes"),
        custom_deserializer=lambda content: yaml.safe_load(content),
        custom_serializer=lambda cfg: yaml.dump(cfg),
    )
    ```
    """
    if config_type is None and (custom_deserializer is None or custom_serializer is None):
        raise OperationValueError("Either provide both custom deserializer and serializer or use config_type")
    if config_type is not None and (custom_deserializer is not None or custom_serializer is not None):
        logger.warning("When using config_type, custom deserializer and serializer are ignored")

    if config_type is not None:
        yield from modify_structured_config._inner(
            path=path,
            modify_action=lambda cfg: modify_action(DictWrapper(cfg) if isinstance(cfg, dict) else ListWrapper(cfg)),
            config_type=config_type,
            backup=backup,
            max_file_size_mb=max_file_size_mb,
        )
    else:
        yield from modify_custom_config._inner(
            path=path,
            modify_action=lambda cfg: modify_action(custom_deserializer(cfg) if isinstance(cfg, str) else cfg),
            deserializer=custom_deserializer,
            serializer=custom_serializer,
            backup=backup,
            max_file_size_mb=max_file_size_mb,
        )


@operation()
def modify_structured_config(
    path: str,
    modify_action: Callable[[dict | list], dict | list],
    config_type: ConfigType = ConfigType.JSON,
    backup: bool = False,
    max_file_size_mb: int = 2,
):
    """
    Modify a structured config file on the remote host.
    Config file would be loaded from the remote host, modified, and then uploaded back to the remote host.

    @note If the config file is too large, this operation will be slow.

    @param path: The path to the config file.
    @param modify_action: A function that modifies config and returns modified value.
    @param config_type: The type of the config file.
    @param backup: Whether to create a backup of the config file before modifying it.
    @param max_file_size_mb: Max allowed size of the config file in MB.

    ```
    def modify_dict(cfg: dict) -> dict:
        cfg["cars"]["car0"] = "Mercedes"
        return cfg

    structured_config.modify_config(
        path="/file.json",
        modify_action=modify_dict,
    )
    ```
    """

    def deserialize(config_str: str) -> dict | list:
        config = None
        match config_type:
            case _ if not config_str.strip():  # is empty or whitespace
                config = {}
            case ConfigType.JSON:
                config = _deserialize(config_str, json.loads)
            case ConfigType.INI:
                config = _deserialize(config_str, _deserialize_ini)
            case ConfigType.XML:
                config = _deserialize(config_str, xmltodict.parse)
            case ConfigType.PLIST:
                config = _deserialize(config_str, lambda content: plistlib.loads(content.encode("utf-8")))
        if not isinstance(config, (dict, list)):
            raise OperationError(
                # todo: good example of real exceptions (the one that should never happen) in contrast to "expected" exceptions
                f"Failure during deserialization. Config must be a dict or a list. This is not supposed to happen. Report a bug."
            )
        return config

    def modify(config: dict | list) -> dict | list:
        result = modify_action(copy.deepcopy(config))
        if not isinstance(result, (dict, list)):
            raise OperationError(f"modify_action must return a dict or a list, got {type(result)}")
        return result

    def serialize(modified_config: dict | list) -> str:
        modified_config_str: str | None = None
        match config_type:
            case ConfigType.JSON:
                modified_config_str = _serialize(modified_config, lambda cfg: json.dumps(cfg, indent=4))
            case ConfigType.INI:
                modified_config_str = _serialize(modified_config, _serialize_ini)
            case ConfigType.XML:
                modified_config_str = _serialize(modified_config, lambda cfg: xmltodict.unparse(cfg, pretty=True))
            case ConfigType.PLIST:
                modified_config_str = _serialize(modified_config, lambda cfg: plistlib.dumps(cfg).decode("utf-8"))
        if modified_config_str is None:
            # todo: remove after testing
            raise OperationError(f"Failure while serializing config file. This is not supposed to happen. Report a bug.")
        return modified_config_str

    yield from modify_custom_config._inner(
        path=path,
        modify_action=modify,
        deserializer=deserialize,
        serializer=serialize,
        backup=backup,
        max_file_size_mb=max_file_size_mb,
    )


@operation()
def modify_plaintext_file(
    path: str,
    modify_action: Callable[[str], str],
    backup: bool = False,
    max_file_size_mb: int = 2,
):
    """
    Modify a plaintext config file on the remote host.
    Config file would be loaded from the remote host, modified, and then uploaded back to the remote host.

    @note If the config file is too large, this operation will be slow.

    @param modify_action: A function that modifies config and returns it.
    @param path: The path to the config file.
    @param backup: Whether to create a backup of the config file before modifying it.
    @param max_file_size_mb: The maximum allowed size of the config file in MB.

    Usage:
    ```
    structured_config.modify_plaintext_file(
        path="/file.txt",
        modify_action=lambda content: content.replace("old", "new"),
    )
    ```
    """
    yield from modify_custom_config(
        path=path,
        modify_action=modify_action,
        deserializer=lambda content: content,
        serializer=lambda cfg: cfg,
        backup=backup,
        max_file_size_mb=max_file_size_mb,
    )


@operation()
def modify_custom_config(
    path: str,
    modify_action: Callable[[TDeserialized], TSerialize],
    deserializer: Callable[[str], TDeserialized],
    serializer: Callable[[TSerialize], str],
    backup: bool = False,
    max_file_size_mb: int = 2,
):
    """
    Modify a custom structured config file on the remote host.
    Config file would be loaded from the remote host, modified, and then uploaded back to the remote host.

    @note If the config file is too large, this operation will be slow.

    @param modify_action: A function that modifies config and returns it.
    @param path: The path to the config file.
    @param deserializer: A function that deserializes the config file content to a dict.
    @param serializer: A function that serializes the config dict to a string.
    @param backup: Whether to create a backup of the config file before modifying it.
    @param max_file_size_mb: The maximum allowed size of the config file in MB.

    Usage:
    ```
    import yaml
    def modify_yaml(cfg: dict) -> dict:
        cfg["cars"]["car0"] = "Mercedes"
        return cfg

    structured_config.modify_custom_config(
        path="/file.yaml",
        modify_action=modify_yaml,
        deserializer=lambda content: yaml.safe_load(content),
        serializer=lambda cfg: yaml.dump(cfg),
    )
    ```
    """
    # validation
    # todo: exceptions or log errors?
    yield FunctionCommand(lambda: _validate_file_state(path, max_file_size_mb), (), {})  # delay, in case file is not present yet

    # load file
    config_str: str = host.get_fact(files_fact.FileContent, path=path)
    if config_str is None:
        raise OperationError(f"Failed to read config file {path}")

    # deserialize
    try:
        config = deserializer(config_str)
    except Exception as e:
        raise OperationError(f"Error while deserializing: {repr(e)}")

    # modify
    try:
        modified_config = modify_action(config)
    except Exception as e:
        raise OperationError(f"modify_action failed: {repr(e)}\n{traceback.format_exc()}")

    # serialize
    try:
        modified_config_str = serializer(modified_config)
    except Exception as e:
        raise OperationError(f"Error while serializing: {repr(e)}")

    # upload
    if modified_config_str == config_str:
        host.noop(f"Config file {path} is already up-to-date")
        return
    if backup:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        yield from files.put._inner(src=StringIO(config_str), dest=f"{path}.bak_{timestamp}")
    yield from files.put._inner(src=StringIO(modified_config_str), dest=path)
