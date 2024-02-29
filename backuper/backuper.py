import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil


# used terms:
# - config: thing written by user, describing what to backup/restore
# - target: file or directory to backup/restore
# - backup: backup of a target

# pipeline:
# 1. get configs (by searching for config.yml files in dirs)
# 2. do BACKUP/RESTORE
# 3. create result summary

# BACKUP pipeline:
# 1. for each config:
#     1.1. ensure target exists
#     1.2. delete old backup
#     1.3. copy target to backup

# RESTORE pipeline:
# 1. for each config:
#     1.1. ensure backup exists
#     1.2. ensure a path to target parent dir exists
#     1.3. rename old target to target.old_restored
#     1.4. copy backup to a path

# execution model:
# - functional, parallel, based on pipeline pattern (stream processing)
# - exceptions are replaced with result items
# - each step is applied to array of configs (items)
# - item is a thing describing one unit of backup/restore in current context
# - items are of different type, for example, Config, PathCheckResult, etc
# - items are piped through steps, each step is a function that takes item and return item
# - items with result of previous step are passed to next step
# - failed items are stored to be shown in summary


# pipeline by types:
# 1. load: dir_path -> RawConfig[] -> ImportedItem[]
# 2. backup: ImportedItem -> BackupItem -> (BackupItem, BackupPreCheckResult) -> (BackupItem, CopyResult) -> (BackupItem, BackupVerificationResult) -> BackupResult -> ActionResult
# 3. restore: ImportedItem -> RestoreItem -> (RestoreItem, RestorePreCheckResult) -> (RestoreItem, CopyResult) -> (RestoreItem, RestoreVerificationResult) -> (RestoreItem, PostRestoreResult) -> RestoreResult -> ActionResult
# 4. summary: ActionResult[] -> Summary


# region data classes

@dataclass
class TargetAndPostRestore:
    TargetPath: Path
    PostRestorePyFile: Path | None


@dataclass
class RawConfig:
    ConfigPath: Path
    TargetAndPostRestore: TargetAndPostRestore | list[TargetAndPostRestore]


@dataclass
class ImportedItem:
    TargetPath: Path
    BackupPath: Path
    PostRestorePyFile: Path | None


@dataclass
class BackupItem:
    TargetPath: Path
    BackupPath: Path


@dataclass
class RestoreItem:
    TargetPath: Path
    BackupPath: Path
    PostRestorePyFile: Path | None


class BackupPreCheckResult(Enum):
    OK = 1
    TargetNotFound = 2


class CopyResultStatus(Enum):
    OK = 1
    Exception = 2


@dataclass
class CopyResult:
    Status: CopyResultStatus
    Exception: Exception | None


class BackupVerificationResult(Enum):
    OK = 1
    BackupNotFound = 2


class RestorePreCheckResult(Enum):
    OK = 1
    BackupNotFound = 2
    TargetParentNotFound = 3


class RestoreVerificationResult(Enum):
    OK = 1
    OkButOldTargetCopyNotFound = 2
    TargetNotFound = 3


class PostRestoreStatus(Enum):
    OK = 1
    Error = 2


@dataclass
class PostRestoreError:
    ErrorCode: int
    ErrorMessage: str


@dataclass
class PostRestoreResult:
    Status: PostRestoreStatus
    Error: PostRestoreError | None


# todo remove
class RestoreResult(Enum):
    OK = 1
    BackupNotFound = 2
    TargetParentNotFound = 3
    PostRestoreError = 4


# endregion


def rm(path: Path) -> None:
    if path.is_file():
        os.remove(path)
    else:
        shutil.rmtree(path)


def backup(item: BackupItem) -> BackupPreCheckResult:
    if not item.TargetPath.exists():
        return BackupPreCheckResult.TargetNotFound

    if item.BackupPath.exists():
        rm(item.BackupPath)

    if item.TargetPath.is_file():
        shutil.copy(item.TargetPath, item.BackupPath)
    else:
        shutil.copytree(item.TargetPath, item.BackupPath)

    return BackupPreCheckResult.OK


def restore(item: RestoreItem) -> RestoreResult:
    if not item.BackupPath.exists():
        return RestoreResult.BackupNotFound

    target_parent = item.TargetPath.parent
    if not target_parent.exists():
        return RestoreResult.TargetParentNotFound

    if item.TargetPath.exists():
        old_name = item.TargetPath.stem + ".old_restored" + item.TargetPath.suffix
        if (target_parent / old_name).exists():
            rm(target_parent / old_name)
        os.rename(item.TargetPath, target_parent / old_name)

    if item.BackupPath.is_file():
        shutil.copy(item.BackupPath, item.TargetPath)
    else:
        shutil.copytree(item.BackupPath, item.TargetPath)

    if item.PostRestorePyFile:
        try:
            subprocess.run(["python", item.PostRestorePyFile, item.TargetPath], check=True)
        except subprocess.CalledProcessError:
            return RestoreResult.PostRestoreError

    return RestoreResult.OK


def load_configs(dir_path: Path) -> list[RawConfig]:
    # todo
    # config.yml files are searched in dir_path and its 1st level sub-dirs
    return []


def import_config(raw_config: RawConfig) -> list[ImportedItem]:
    # todo
    # raw_config is converted to list of ImportedConfigItem
    return []


def entry_point() -> None:
    # 0. parse args
    # 1. load configs from dirs
    # 2. import configs
    # 3. do pre-checks
    # 4. do backup/restore
    # 5. verify results
    # 6. create summary
    return
