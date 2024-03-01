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


# region common


@dataclass
class ImportedItem:
    TargetPath: Path
    BackupPath: Path
    PostRestorePyFile: Path | None


class FileManipulationStatus(Enum):
    OK = 1
    Exception = 2


@dataclass
class FileManipulationResult:
    Status: FileManipulationStatus
    Exception: Exception | None


class ActionStatus(Enum):
    OK = 1
    Error = 2
    DryRun = 3


@dataclass
class ActionResult:
    TargetPath: Path
    Status: ActionStatus
    ErrorText: str | None


class ActionType(Enum):
    Backup = 1
    Restore = 2


@dataclass
class Mode:
    ActionType: ActionType
    IsDryRun: bool


def _rm(path: Path) -> None:
    if path.is_file():
        os.remove(path)
    else:
        shutil.rmtree(path)


# endregion


class ConfigLoader:
    CONFIG_NAME = 'config.json'

    raw_config_target_path_json_key = "path"
    raw_config_post_restore_py_file_json_key = "post_restore_py_file"

    @dataclass
    class ConfigItem:
        TargetPath: Path
        PostRestorePyFile: Path | None

    @dataclass
    class ConfigLoadError:
        ConfigPath: Path
        Error: Exception

    @staticmethod
    def _get_content_from_json(data: dict) -> ConfigItem | list[ConfigItem]:
        if isinstance(data, list):
            return [ConfigLoader._get_content_from_json(item) for item in data]

        post_restore_py_file = Path(data[ConfigLoader.raw_config_post_restore_py_file_json_key]) \
            if ConfigLoader.raw_config_post_restore_py_file_json_key in data \
            else None
        return ConfigLoader.ConfigItem(
            Path(data[ConfigLoader.raw_config_target_path_json_key]),
            post_restore_py_file
        )

    @staticmethod
    def load_configs(directory: Path) -> list[ImportedItem | ConfigLoadError]:
        @dataclass
        class LoadedConfig:
            ConfigPath: Path
            Content: ConfigLoader.ConfigItem | list[ConfigLoader.ConfigItem]

        config_files: list[Path] = []
        for child in directory.iterdir():
            if child.is_file() and child.name == ConfigLoader.CONFIG_NAME:
                config_files.append(child)
            if child.is_dir() and (child / ConfigLoader.CONFIG_NAME).exists():
                config_files.append(child / ConfigLoader.CONFIG_NAME)

        loaded_configs: list[LoadedConfig] = []
        failed_configs: list[ConfigLoader.ConfigLoadError] = []
        for config_file in config_files:
            with open(config_file, 'r') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    failed_configs.append(ConfigLoader.ConfigLoadError(config_file, e))
                    continue
                loaded_configs.append(LoadedConfig(config_file, ConfigLoader._get_content_from_json(data)))

        imported_configs: list[ImportedItem] = []
        for loaded_config in loaded_configs:
            if isinstance(loaded_config.Content, list):
                imported_configs += [ImportedItem(
                    item.TargetPath,
                    loaded_config.ConfigPath.parent / item.TargetPath.name,
                    item.PostRestorePyFile
                ) for item in loaded_config.Content]
                continue
            if isinstance(loaded_config.Content, ConfigLoader.ConfigItem):
                imported_configs.append(ImportedItem(
                    loaded_config.Content.TargetPath,
                    loaded_config.ConfigPath.parent / loaded_config.Content.TargetPath.name,
                    loaded_config.Content.PostRestorePyFile
                ))
                continue
            raise ValueError(f"Unknown config content type: {loaded_config.Content}")

        return imported_configs + failed_configs


class SimilarityVerifier:
    @staticmethod
    def _get_directory_info(directory: Path) -> tuple[int, int]:
        assert directory.is_dir(), "Path must be a directory"
        total_size = 0
        file_count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        return total_size, file_count

    @staticmethod
    def _hash_file(filepath: Path) -> str:
        assert filepath.is_file(), "Path must be a file"
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _are_dirs_same(dir1: Path, dir2: Path) -> bool:
        assert dir1.is_dir() and dir2.is_dir(), "Both paths must be directories"
        if dir1.stat().st_size != dir2.stat().st_size:
            return False
        return SimilarityVerifier._get_directory_info(dir1) == SimilarityVerifier._get_directory_info(dir2)

    @staticmethod
    def _are_files_same(file1: Path, file2: Path) -> bool:
        assert file1.is_file() and file2.is_file(), "Both paths must be files"
        if file1.stat().st_size != file2.stat().st_size:
            return False
        return SimilarityVerifier._hash_file(file1) == SimilarityVerifier._hash_file(file2)

    @staticmethod
    def verify_same(path1: Path, path2: Path) -> bool:
        if path1.is_file() and path2.is_file():
            return SimilarityVerifier._are_files_same(path1, path2)
        if path1.is_dir() and path2.is_dir():
            return SimilarityVerifier._are_dirs_same(path1, path2)
        return False


class Backuper:
    @dataclass
    class BackupItem:
        TargetPath: Path
        BackupPath: Path

    class _BackupVerificationResult(Enum):
        OK = 1
        BackupNotFound = 2
        BackupDifferentThanTarget = 3

    class _BackupPreCheckResult(Enum):
        OK = 1
        TargetNotFound = 2

    @staticmethod
    def _backup_pre_check(item: BackupItem) -> _BackupPreCheckResult:
        return Backuper._BackupPreCheckResult.OK \
            if item.TargetPath.exists() \
            else Backuper._BackupPreCheckResult.TargetNotFound

    @staticmethod
    def _backup_process_files(item: BackupItem) -> FileManipulationResult:
        try:
            if item.BackupPath.exists():
                _rm(item.BackupPath)

            if item.TargetPath.is_file():
                shutil.copy(item.TargetPath, item.BackupPath)
            else:
                shutil.copytree(item.TargetPath, item.BackupPath)

            return FileManipulationResult(FileManipulationStatus.OK, None)
        except Exception as e:
            return FileManipulationResult(FileManipulationStatus.Exception, e)

    @staticmethod
    def _backup_verify(item: BackupItem) -> _BackupVerificationResult:
        if not item.BackupPath.exists():
            return Backuper._BackupVerificationResult.BackupNotFound

        return Backuper._BackupVerificationResult.OK \
            if SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath) \
            else Backuper._BackupVerificationResult.BackupDifferentThanTarget

    @staticmethod
    def backup(items: list[BackupItem], is_dry_run: bool) -> list[ActionResult]:
        pre_check_failed: list[tuple[Backuper.BackupItem, Backuper._BackupPreCheckResult]] = []
        process_files_failed: list[tuple[Backuper.BackupItem, FileManipulationResult]] = []
        verify_failed: list[tuple[Backuper.BackupItem, Backuper._BackupVerificationResult]] = []
        dry_run: list[Backuper.BackupItem] = []
        success: list[Backuper.BackupItem] = []

        for item in items:
            pre_check_result = Backuper._backup_pre_check(item)
            if pre_check_result != Backuper._BackupPreCheckResult.OK:
                pre_check_failed.append((item, pre_check_result))
                continue

            if is_dry_run:
                dry_run.append(item)
                continue

            process_files_result = Backuper._backup_process_files(item)
            if process_files_result.Status != FileManipulationStatus.OK:
                process_files_failed.append((item, process_files_result))
                continue

            verify_result = Backuper._backup_verify(item)
            if verify_result != Backuper._BackupVerificationResult.OK:
                verify_failed.append((item, verify_result))
                continue

            success.append(item)

        return [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Pre-check failed [{result.name}]")
            for item, result in pre_check_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Process files failed [{result.Exception}]")
            for item, result in process_files_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Verify failed [{result.name}]")
            for item, result in verify_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.OK, None)
            for item in success
        ] + [
            ActionResult(item.TargetPath, ActionStatus.DryRun, None)
            for item in dry_run
        ]


class Restorer:
    @dataclass
    class RestoreItem:
        TargetPath: Path
        BackupPath: Path
        PostRestorePyFile: Path | None

    class _RestorePreCheckResult(Enum):
        OK = 1
        BackupNotFound = 2
        TargetParentNotFound = 3

    class _RestoreVerificationResult(Enum):
        OK = 1
        OkButOldTargetCopyNotFound = 2
        TargetNotFound = 3
        BackupDifferentThanTarget = 4

    @dataclass
    class _PostRestoreResult:
        class _PostRestoreStatus(Enum):
            OK = 1
            Error = 2

        @dataclass
        class _PostRestoreError:
            ErrorCode: int
            ErrorMessage: str

        Status: _PostRestoreStatus
        Error: _PostRestoreError | None

    @staticmethod
    def _restore_pre_check(item: RestoreItem) -> _RestorePreCheckResult:
        if not item.BackupPath.exists():
            return Restorer._RestorePreCheckResult.BackupNotFound

        if not item.TargetPath.parent.exists():
            return Restorer._RestorePreCheckResult.TargetParentNotFound

        return Restorer._RestorePreCheckResult.OK

    @staticmethod
    def _restore_process_files(item: RestoreItem) -> FileManipulationResult:
        try:
            if item.TargetPath.exists():
                old_name = item.TargetPath.stem + ".old_restored" + item.TargetPath.suffix
                if (item.TargetPath.parent / old_name).exists():
                    _rm(item.TargetPath.parent / old_name)
                os.rename(item.TargetPath, item.TargetPath.parent / old_name)

            if item.BackupPath.is_file():
                shutil.copy(item.BackupPath, item.TargetPath)
            else:
                shutil.copytree(item.BackupPath, item.TargetPath)
            return FileManipulationResult(FileManipulationStatus.OK, None)
        except Exception as e:
            return FileManipulationResult(FileManipulationStatus.Exception, e)

    @staticmethod
    def _restore_verify(item: RestoreItem) -> _RestoreVerificationResult:
        if not item.TargetPath.exists():
            return Restorer._RestoreVerificationResult.TargetNotFound

        return Restorer._RestoreVerificationResult.OK \
            if SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath) \
            else Restorer._RestoreVerificationResult.BackupDifferentThanTarget

    @staticmethod
    def _run_post_restore_py(item: RestoreItem) -> _PostRestoreResult:
        # noinspection PyPep8Naming,PyProtectedMember
        statusType = Restorer._PostRestoreResult._PostRestoreStatus
        # noinspection PyPep8Naming,PyProtectedMember
        errorType = Restorer._PostRestoreResult._PostRestoreError

        assert item.PostRestorePyFile is not None, "PostRestorePyFile must be set"
        assert item.PostRestorePyFile.exists(), "PostRestorePyFile must exist"
        try:
            subprocess.run(["python", item.PostRestorePyFile, item.TargetPath], check=True)
            return Restorer._PostRestoreResult(statusType.OK, None)
        except subprocess.CalledProcessError as e:
            return Restorer._PostRestoreResult(
                statusType.Error,
                errorType(e.returncode, e.stderr.decode("utf-8"))
            )

    @staticmethod
    def restore(items: list[RestoreItem], is_dry_run: bool) -> list[ActionResult]:
        # noinspection PyPep8Naming,PyProtectedMember
        PostRestoreStatusType = Restorer._PostRestoreResult._PostRestoreStatus

        pre_check_failed: list[tuple[Restorer.RestoreItem, Restorer._RestorePreCheckResult]] = []
        process_files_failed: list[tuple[Restorer.RestoreItem, FileManipulationResult]] = []
        verify_failed: list[tuple[Restorer.RestoreItem, Restorer._RestoreVerificationResult]] = []
        post_restore_failed: list[tuple[Restorer.RestoreItem, Restorer._PostRestoreResult]] = []
        success: list[Restorer.RestoreItem] = []
        dry_run: list[Restorer.RestoreItem] = []

        for item in items:
            pre_check_result = Restorer._restore_pre_check(item)
            if pre_check_result != Restorer._RestorePreCheckResult.OK:
                pre_check_failed.append((item, pre_check_result))
                continue

            if is_dry_run:
                dry_run.append(item)
                continue

            process_files_result = Restorer._restore_process_files(item)
            if process_files_result.Status != FileManipulationStatus.OK:
                process_files_failed.append((item, process_files_result))
                continue

            verify_result = Restorer._restore_verify(item)
            if verify_result != Restorer._RestoreVerificationResult.OK:
                verify_failed.append((item, verify_result))
                continue

            if item.PostRestorePyFile is not None:
                post_restore_result = Restorer._run_post_restore_py(item)
                if post_restore_result.Status != PostRestoreStatusType.OK:
                    post_restore_failed.append((item, post_restore_result))
                    continue

            success.append(item)

        return [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Pre-check failed [{result}]")
            for item, result in pre_check_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Process files failed [{result.Exception}]")
            for item, result in process_files_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Verify failed [{result}]")
            for item, result in verify_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.Error, f"Post-restore failed [{result.Error}]")
            for item, result in post_restore_failed
        ] + [
            ActionResult(item.TargetPath, ActionStatus.OK, None)
            for item in success
        ] + [
            ActionResult(item.TargetPath, ActionStatus.DryRun, None)
            for item in dry_run
            if is_dry_run
        ]


class CLI:
    @staticmethod
    def _parse_args() -> tuple[Path, Mode]:
        parser = argparse.ArgumentParser(description='Backup/restore files and directories')
        parser.add_argument('mode', type=str, help='Mode: backup, restore', choices=['backup', 'restore'])
        parser.add_argument('--dir', type=str, help='Directory with config files', default='.')
        parser.add_argument('--dry-run', action='store_true', help='Dry run')
        args = parser.parse_args()

        return Path(args.dir), Mode(ActionType[args.mode.capitalize()], args.dry_run)

    @staticmethod
    def _create_summary(results: list[ActionResult]) -> str:
        # todo
        return ""

    @staticmethod
    def cli_entry_point() -> None:
        directory, mode = CLI._parse_args()
        directory = directory.resolve()

        print(
            'Starting...',
            f'Directory: {directory}',
            f'Mode: {mode.ActionType.name}',
            'Dry run' if mode.IsDryRun else '',
            sep='\n'
        )

        # todo: check permissions and directory/ies existence
        if not directory.is_dir():
            print('\n' + f'Directory {directory} does not exist, exiting...')
            return
        if not os.access(directory, os.R_OK):
            print('\n' + f'Directory {directory} is not readable, exiting...')
            return

        config_load_results = ConfigLoader.load_configs(directory)
        failed_configs: list[ConfigLoader.ConfigLoadError] = list(filter(lambda x: isinstance(x, ConfigLoader.ConfigLoadError), config_load_results))
        success_configs: list[ImportedItem] = list(filter(lambda x: isinstance(x, ImportedItem), config_load_results))
        if not config_load_results:
            print('\n' + 'No configs found, exiting...')
            return
        print(f'Configs found: {len(config_load_results)}')
        if any(failed_configs):
            print(f'Configs failed to load: {len(failed_configs)}')
            for error, i in zip(failed_configs, range(len(failed_configs))):
                print(f'\t{i + 1}. {error.ConfigPath} [{error.Error}]')
            print(f'Configs loaded: {len(success_configs)}')
        else:
            print('All configs loaded successfully')

        print('Starting processing...')
        results = run(mode, success_configs)
        print('Processing finished')

        success_results = list(filter(lambda x: x.Status == ActionStatus.OK, results))
        failed_results = list(filter(lambda x: x.Status == ActionStatus.Error, results))
        dry_run_results = list(filter(lambda x: x.Status == ActionStatus.DryRun, results))
        print(
            f'Success: {len(success_results)}',
            f'Failed: {len(failed_results)}',
            f'Dry run: {len(dry_run_results)}',
            sep='\n'
        )
        if any(failed_results):
            for error, i in zip(failed_results, range(len(failed_results))):
                print(f'\t{i + 1}. {error.ErrorText}')
        # summary = create_summary(results)
        # print(summary)


def run(mode: Mode, configs: list[ImportedItem]) -> list[ActionResult]:
    configs = map(lambda x: ImportedItem(
        Path(os.path.expanduser(x.TargetPath)).resolve(),
        Path(os.path.expanduser(x.BackupPath)).resolve(),
        Path(os.path.expanduser(x.PostRestorePyFile)).resolve() if x.PostRestorePyFile is not None else None
    ), configs)

    if mode.ActionType == ActionType.Backup:
        items = [Backuper.BackupItem(item.TargetPath, item.BackupPath) for item in configs]
        return Backuper.backup(items, mode.IsDryRun)

    if mode.ActionType == ActionType.Restore:
        items = [Restorer.RestoreItem(item.TargetPath, item.BackupPath, item.PostRestorePyFile) for item in configs]
        return Restorer.restore(items, mode.IsDryRun)

    raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    CLI.cli_entry_point()
