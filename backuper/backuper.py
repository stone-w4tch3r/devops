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


# todo: check shutil rm/copy/move functions for compatibility with files and dirs


@dataclass
class TargetAndPostRestore:
    TargetPath: Path
    PostRestorePyFile: Path | None


@dataclass
class RawConfig:
    ConfigPath: Path
    TargetAndPostRestore: TargetAndPostRestore | list[TargetAndPostRestore]


@dataclass
class ImportedConfigItem:
    TargetPath: Path
    BackupPath: Path
    PostRestorePyFile: Path | None


@dataclass
class ToBackupItem:
    TargetPath: Path
    BackupPath: Path


class BackupResultType(Enum):
    OK = 1
    TargetNotFound = 2


@dataclass
class BackupResult:
    TargetPath: Path
    BackupPath: Path
    Result: BackupResultType


def backup(item: ToBackupItem) -> BackupResult:
    if not item.TargetPath.exists():
        return BackupResult(item.TargetPath, item.BackupPath, BackupResultType.TargetNotFound)

    if item.BackupPath.exists():
        if item.BackupPath.is_file():
            os.remove(item.BackupPath)
        else:
            shutil.rmtree(item.BackupPath)

    if item.TargetPath.is_file():
        shutil.copy(item.TargetPath, item.BackupPath)
    else:
        shutil.copytree(item.TargetPath, item.BackupPath)

    return BackupResult(item.TargetPath, item.BackupPath, BackupResultType.OK)


class RestoreResultType(Enum):
    OK = 1
    BackupNotFound = 2
    TargetParentNotFound = 3
    PostRestoreError = 4


@dataclass
class RestoreResult:
    TargetPath: Path
    BackupPath: Path
    Result: RestoreResultType


def restore(item: ImportedConfigItem) -> RestoreResult:
    if not item.BackupPath.exists():
        return RestoreResult(item.TargetPath, item.BackupPath, RestoreResultType.BackupNotFound)

    target_parent = item.TargetPath.parent
    if not target_parent.exists():
        return RestoreResult(item.TargetPath, item.BackupPath, RestoreResultType.TargetParentNotFound)

    if item.TargetPath.exists():
        old_name = item.TargetPath.stem + ".old_restored" + item.TargetPath.suffix
        if (target_parent / old_name).exists():
            shutil.rmtree(target_parent / old_name)
        os.rename(item.TargetPath, target_parent / old_name)

    if item.BackupPath.is_file():
        shutil.copy(item.BackupPath, item.TargetPath)
    else:
        shutil.copytree(item.BackupPath, item.TargetPath)

    if item.PostRestorePyFile:
        try:
            subprocess.run(["python", item.PostRestorePyFile, item.TargetPath], check=True)
        except subprocess.CalledProcessError:
            return RestoreResult(item.TargetPath, item.BackupPath, RestoreResultType.PostRestoreError)

    return RestoreResult(item.TargetPath, item.BackupPath, RestoreResultType.OK)
