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


def backup(config_items: list[ToBackupItem]) -> list[BackupResult]:
    target_not_found = []
    success = []

    for item in config_items:
        if not item.TargetPath.exists():
            target_not_found.append(item)
            continue

        if item.BackupPath.exists():
            shutil.rmtree(item.BackupPath)

        if item.TargetPath.is_file():
            shutil.copy(item.TargetPath, item.BackupPath)
        else:
            shutil.copytree(item.TargetPath, item.BackupPath)

        success.append(item)

    return [
        BackupResult(TargetPath=item.TargetPath, BackupPath=item.BackupPath, Result=BackupResultType.OK)
        for item in success
    ] + [
        BackupResult(TargetPath=item.TargetPath, BackupPath=item.BackupPath, Result=BackupResultType.TargetNotFound)
        for item in target_not_found
    ]


class RestoreResultType(Enum):
    OK = 1
    BackupNotFound = 2
    TargetParentNotFound = 3


@dataclass
class RestoreResult:
    TargetPath: Path
    BackupPath: Path
    Result: RestoreResultType


def restore(config_items: list[ImportedConfigItem]) -> list[RestoreResult]:
    backup_not_found = []
    target_parent_not_found = []
    post_restore_error = []
    success = []

    for item in config_items:
        if not item.BackupPath.exists():
            backup_not_found.append(item)
            continue

        target_parent = item.TargetPath.parent
        if not target_parent.exists():
            target_parent_not_found.append(item)
            continue

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
                post_restore_error.append(item)
                continue

        success.append(item)

    return [
        RestoreResult(TargetPath=item.TargetPath, BackupPath=item.BackupPath, Result=RestoreResultType.OK)
        for item in success
    ] + [
        RestoreResult(TargetPath=item.TargetPath, BackupPath=item.BackupPath, Result=RestoreResultType.BackupNotFound)
        for item in backup_not_found
    ] + [
        RestoreResult(TargetPath=item.TargetPath, BackupPath=item.BackupPath, Result=RestoreResultType.TargetParentNotFound)
        for item in target_parent_not_found
    ]
