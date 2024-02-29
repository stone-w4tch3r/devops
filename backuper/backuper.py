#!/usr/bin/env python3

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil
import hashlib
import json
import argparse


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
# 2. backup: ImportedItem -> BackupItem -> (BackupItem, BackupPreCheckResult) -> (BackupItem, FileManipulationResult) -> (BackupItem, BackupVerificationResult) -> ActionResult
# 3. restore: ImportedItem -> RestoreItem -> (RestoreItem, RestorePreCheckResult) -> (RestoreItem, FileManipulationResult) -> (RestoreItem, RestoreVerificationResult) -> (RestoreItem, PostRestoreResult) -> ActionResult
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
class FileManipulationResult:
    Status: CopyResultStatus
    Exception: Exception | None


class BackupVerificationResult(Enum):
    OK = 1
    BackupNotFound = 2
    BackupDifferentThanTarget = 3


class RestorePreCheckResult(Enum):
    OK = 1
    BackupNotFound = 2
    TargetParentNotFound = 3


class RestoreVerificationResult(Enum):
    OK = 1
    OkButOldTargetCopyNotFound = 2
    TargetNotFound = 3
    BackupDifferentThanTarget = 4


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


class ActionResultStatus(Enum):
    OK = 1
    Error = 2


@dataclass
class ActionResult:
    Status: ActionResultStatus
    ErrorText: str | None


class ActionType(Enum):
    Backup = 1
    Restore = 2


@dataclass
class Mode:
    ActionType: ActionType
    IsDryRun: bool


# endregion


def rm(path: Path) -> None:
    if path.is_file():
        os.remove(path)
    else:
        shutil.rmtree(path)


def get_directory_info(directory: Path) -> tuple[int, int]:
    assert directory.is_dir(), "Path must be a directory"
    total_size = 0
    file_count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_count += 1
    return total_size, file_count


def are_dirs_same(dir1: Path, dir2: Path) -> bool:
    assert dir1.is_dir() and dir2.is_dir(), "Both paths must be directories"
    if dir1.stat().st_size != dir2.stat().st_size:
        return False
    return get_directory_info(dir1) == get_directory_info(dir2)


def hash_file(filepath: Path) -> str:
    assert filepath.is_file(), "Path must be a file"
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def are_files_same(file1: Path, file2: Path) -> bool:
    assert file1.is_file() and file2.is_file(), "Both paths must be files"
    if file1.stat().st_size != file2.stat().st_size:
        return False
    return hash_file(file1) == hash_file(file2)


def backup_pre_check(item: BackupItem) -> BackupPreCheckResult:
    return BackupPreCheckResult.OK \
        if item.TargetPath.exists() \
        else BackupPreCheckResult.TargetNotFound


def backup_process_files(item: BackupItem) -> FileManipulationResult:
    try:
        if item.BackupPath.exists():
            rm(item.BackupPath)

        if item.TargetPath.is_file():
            shutil.copy(item.TargetPath, item.BackupPath)
        else:
            shutil.copytree(item.TargetPath, item.BackupPath)

        return FileManipulationResult(CopyResultStatus.OK, None)
    except Exception as e:
        return FileManipulationResult(CopyResultStatus.Exception, e)


def backup_verify(item: BackupItem) -> BackupVerificationResult:
    if not item.BackupPath.exists():
        return BackupVerificationResult.BackupNotFound

    if item.TargetPath.is_file():
        return BackupVerificationResult.OK \
            if are_files_same(item.TargetPath, item.BackupPath) \
            else BackupVerificationResult.BackupDifferentThanTarget

    return BackupVerificationResult.OK \
        if are_dirs_same(item.TargetPath, item.BackupPath) \
        else BackupVerificationResult.BackupDifferentThanTarget


def restore_pre_check(item: RestoreItem) -> RestorePreCheckResult:
    if not item.BackupPath.exists():
        return RestorePreCheckResult.BackupNotFound

    if not item.TargetPath.parent.exists():
        return RestorePreCheckResult.TargetParentNotFound

    return RestorePreCheckResult.OK


def restore_process_files(item: RestoreItem) -> FileManipulationResult:
    try:
        if item.TargetPath.exists():
            old_name = item.TargetPath.stem + ".old_restored" + item.TargetPath.suffix
            if (item.TargetPath.parent / old_name).exists():
                rm(item.TargetPath.parent / old_name)
            os.rename(item.TargetPath, item.TargetPath.parent / old_name)

        if item.BackupPath.is_file():
            shutil.copy(item.BackupPath, item.TargetPath)
        else:
            shutil.copytree(item.BackupPath, item.TargetPath)
        return FileManipulationResult(CopyResultStatus.OK, None)
    except Exception as e:
        return FileManipulationResult(CopyResultStatus.Exception, e)


def restore_verify(item: RestoreItem) -> RestoreVerificationResult:
    if not item.TargetPath.exists():
        return RestoreVerificationResult.TargetNotFound

    if item.TargetPath.is_file():
        return RestoreVerificationResult.OK \
            if are_files_same(item.TargetPath, item.BackupPath) \
            else RestoreVerificationResult.BackupDifferentThanTarget

    return RestoreVerificationResult.OK \
        if are_dirs_same(item.TargetPath, item.BackupPath) \
        else RestoreVerificationResult.BackupDifferentThanTarget


def run_post_restore_py(item: RestoreItem) -> PostRestoreResult:
    assert item.PostRestorePyFile is not None, "PostRestorePyFile must be set"
    assert item.PostRestorePyFile.exists(), "PostRestorePyFile must exist"
    try:
        subprocess.run(["python", item.PostRestorePyFile, item.TargetPath], check=True)
        return PostRestoreResult(PostRestoreStatus.OK, None)
    except subprocess.CalledProcessError as e:
        return PostRestoreResult(PostRestoreStatus.Error, PostRestoreError(e.returncode, e.stderr.decode("utf-8")))


def backup(items: list[BackupItem], is_dry_run: bool) -> list[ActionResult]:
    pre_check_failed: list[tuple[BackupItem, BackupPreCheckResult]] = []
    process_files_failed: list[tuple[BackupItem, FileManipulationResult]] = []
    verify_failed: list[tuple[BackupItem, BackupVerificationResult]] = []
    success: list[BackupItem] = []

    for item in items:
        pre_check_result = backup_pre_check(item)
        if pre_check_result != BackupPreCheckResult.OK:
            pre_check_failed.append((item, pre_check_result))
            continue

        if is_dry_run:
            continue

        process_files_result = backup_process_files(item)
        if process_files_result.Status != CopyResultStatus.OK:
            process_files_failed.append((item, process_files_result))
            continue

        verify_result = backup_verify(item)
        if verify_result != BackupVerificationResult.OK:
            verify_failed.append((item, verify_result))
            continue

        success.append(item)

    return [
        ActionResult(ActionResultStatus.Error, f"Pre-check failed for {item.TargetPath}: {result}")
        for item, result in pre_check_failed
    ] + [
        ActionResult(ActionResultStatus.Error, f"Process files failed for {item.TargetPath}: {result.Exception}")
        for item, result in process_files_failed
    ] + [
        ActionResult(ActionResultStatus.Error, f"Verify failed for {item.TargetPath}: {result}")
        for item, result in verify_failed
    ] + [
        ActionResult(ActionResultStatus.OK, None)
        for _ in success
    ]


def restore(items: list[RestoreItem], is_dry_run: bool) -> list[ActionResult]:
    pre_check_failed: list[tuple[RestoreItem, RestorePreCheckResult]] = []
    process_files_failed: list[tuple[RestoreItem, FileManipulationResult]] = []
    verify_failed: list[tuple[RestoreItem, RestoreVerificationResult]] = []
    post_restore_failed: list[tuple[RestoreItem, PostRestoreResult]] = []
    success: list[RestoreItem] = []

    for item in items:
        pre_check_result = restore_pre_check(item)
        if pre_check_result != RestorePreCheckResult.OK:
            pre_check_failed.append((item, pre_check_result))
            continue

        if is_dry_run:
            continue

        process_files_result = restore_process_files(item)
        if process_files_result.Status != CopyResultStatus.OK:
            process_files_failed.append((item, process_files_result))
            continue

        verify_result = restore_verify(item)
        if verify_result != RestoreVerificationResult.OK:
            verify_failed.append((item, verify_result))
            continue

        if item.PostRestorePyFile is not None:
            post_restore_result = run_post_restore_py(item)
            if post_restore_result.Status != PostRestoreStatus.OK:
                post_restore_failed.append((item, post_restore_result))
                continue

        success.append(item)

    return [
        ActionResult(ActionResultStatus.Error, f"Pre-check failed for {item.TargetPath}: {result}")
        for item, result in pre_check_failed
    ] + [
        ActionResult(ActionResultStatus.Error, f"Process files failed for {item.TargetPath}: {result.Exception}")
        for item, result in process_files_failed
    ] + [
        ActionResult(ActionResultStatus.Error, f"Verify failed for {item.TargetPath}: {result}")
        for item, result in verify_failed
    ] + [
        ActionResult(ActionResultStatus.Error, f"Post-restore failed for {item.TargetPath}: {result.Error}")
        for item, result in post_restore_failed
    ] + [
        ActionResult(ActionResultStatus.OK, None)
        for _ in success
    ]


def load_configs(directory: Path) -> list[RawConfig]:
    config_name = 'config.json'
    configs: list[Path] = []
    for child in directory.iterdir():
        if child.is_file() and child.name == config_name:
            configs.append(child)
        if child.is_dir() and (child / config_name).exists():
            configs.append(child / config_name)

    # todo: add invalid config handling
    raw_configs = []
    for config_file in configs:
        with open(config_file, 'r') as f:
            data = json.load(f)
            raw_configs.append(RawConfig(config_file, data))

    return raw_configs


def import_config(raw_config: RawConfig) -> list[ImportedItem]:
    # todo: what if same file names?
    if isinstance(raw_config.TargetAndPostRestore, list):
        return [ImportedItem(
            target.TargetPath,
            raw_config.ConfigPath.parent / target.TargetPath.name,
            target.PostRestorePyFile
        ) for target in raw_config.TargetAndPostRestore]

    return [ImportedItem(
        raw_config.TargetAndPostRestore.TargetPath,
        raw_config.ConfigPath.parent / raw_config.TargetAndPostRestore.TargetPath.name,
        raw_config.TargetAndPostRestore.PostRestorePyFile
    )]


def parse_args() -> tuple[Path, Mode]:
    parser = argparse.ArgumentParser(description='Backup/restore files and directories')
    parser.add_argument('mode', type=str, help='Mode: backup, restore', choices=['backup', 'restore'])
    parser.add_argument('--dir', type=str, help='Directory with config files', default='.')
    parser.add_argument('--dry-run', action='store_true', help='Dry run')
    args = parser.parse_args()

    return Path(args.dir), Mode(ActionType[args.mode.capitalize()], args.dry_run)


def run(mode: Mode, configs: list[ImportedItem]) -> list[ActionResult]:
    if mode.ActionType == ActionType.Backup:
        items = [BackupItem(item.TargetPath, item.BackupPath) for item in configs]
        return backup(items, mode.IsDryRun)

    if mode.ActionType == ActionType.Restore:
        items = [RestoreItem(item.TargetPath, item.BackupPath, item.PostRestorePyFile) for item in configs]
        return restore(items, mode.IsDryRun)

    raise ValueError(f"Unknown mode: {mode}")


def create_summary(results: list[ActionResult]) -> str:
    # todo
    return ""


def cli_entry_point() -> None:
    directory, mode = parse_args()
    print('Starting...')
    print(f'Directory: {directory}, mode: {mode.ActionType.name}' + (', dry run' if mode.IsDryRun else ''))
    # raw_configs = load_configs(directory)
    # imported_configs = [imported_item for raw_config in raw_configs for imported_item in import_config(raw_config)]
    # results = run(mode, imported_configs)
    # summary = create_summary(results)
    # print(summary)


if __name__ == "__main__":
    cli_entry_point()
