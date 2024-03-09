#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


# region public


@dataclass
class ImportedItem:
    TargetPath: Path
    BackupPath: Path
    PostRestorePyFile: Path | None


class ActionStatus(Enum):
    OK = 1
    Error = 2
    DryRun = 3


@dataclass
class ActionResult:
    TargetPath: Path
    BackupPath: Path
    Status: ActionStatus
    ErrorText: str | None


class ActionType(Enum):
    Backup = 1
    Restore = 2


@dataclass
class Mode:
    ActionType: ActionType
    IsDryRun: bool


def run(mode: Mode, configs: list[ImportedItem]) -> list[ActionResult]:
    configs = map(
        lambda x: ImportedItem(
            Path(os.path.expanduser(x.TargetPath)).resolve(),
            Path(os.path.expanduser(x.BackupPath)).resolve(),
            Path(os.path.expanduser(x.PostRestorePyFile)).resolve() if x.PostRestorePyFile is not None else None
        ), configs
    )

    if mode.ActionType == ActionType.Backup:
        items = [_Backuper.BackupItem(item.TargetPath, item.BackupPath) for item in configs]
        return [_Backuper.backup(item, mode.IsDryRun) for item in items]

    if mode.ActionType == ActionType.Restore:
        items = [_Restorer.RestoreItem(config.TargetPath, config.BackupPath) for config in configs]
        restored = [_Restorer.restore(item, mode.IsDryRun) for item in items]

        restored_and_config = [(r, c) for r in restored for c in configs if r.TargetPath == c.TargetPath]
        not_to_execute: list[ActionResult] = filter(
            lambda x: x[0].Status not in [ActionStatus.OK, ActionStatus.DryRun] or x[1].PostRestorePyFile is None,
            restored_and_config
        )
        to_execute: list[ImportedItem] = filter(
            lambda x: x[0].Status in [ActionStatus.OK, ActionStatus.DryRun] and x[1].PostRestorePyFile is not None,
            restored_and_config
        )
        execution_results = [
            ActionResult(r.TargetPath, backup_path, r.Status, r.ErrorText)
            for x in to_execute
            for r, backup_path in
            (_PyExecutor.execute_py(x.TargetPath, x.PostRestorePyFile, mode.IsDryRun), x.BackupPath)
        ]

        return not_to_execute + execution_results

    raise ValueError(f"Unknown mode: {mode}")


# endregion


# region common


class _FileManipulationStatus(Enum):
    OK = 1
    Exception = 2


@dataclass
class _FileManipulationResult:
    Status: _FileManipulationStatus
    Exception: Exception | None


def _rm(path: Path) -> None:
    if path.is_file():
        os.remove(path)
    else:
        shutil.rmtree(path)


def _is_write_allowed(path: Path) -> bool:
    return path.exists() and os.access(path, os.W_OK)


def _is_read_allowed(path: Path) -> bool:
    return (path.exists()
            and os.access(path, os.R_OK)
            and all([_is_read_allowed(p) for p in path.iterdir() if p.is_dir()]))


# endregion


class _SimilarityVerifier:
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
        return _SimilarityVerifier._get_directory_info(dir1) == _SimilarityVerifier._get_directory_info(dir2)

    @staticmethod
    def _are_files_same(file1: Path, file2: Path) -> bool:
        assert file1.is_file() and file2.is_file(), "Both paths must be files"
        if file1.stat().st_size != file2.stat().st_size:
            return False
        return _SimilarityVerifier._hash_file(file1) == _SimilarityVerifier._hash_file(file2)

    @staticmethod
    def verify_same(path1: Path, path2: Path) -> bool:
        if path1.is_file() and path2.is_file():
            return _SimilarityVerifier._are_files_same(path1, path2)
        if path1.is_dir() and path2.is_dir():
            return _SimilarityVerifier._are_dirs_same(path1, path2)
        return False


class _Backuper:
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
        PermissionsError_TargetReadable_BackupNotWritable = 3
        PermissionsError_TargetNotReadable_BackupWritable = 4
        PermissionsError_TargetNotReadable_BackupNotWritable = 5

    _verification_result_to_str_map = {
        _BackupVerificationResult.OK: "OK",
        _BackupVerificationResult.BackupNotFound: "Backup not found",
        _BackupVerificationResult.BackupDifferentThanTarget: "Backup different than target"
    }

    _pre_check_result_to_str_map = {
        _BackupPreCheckResult.OK: "OK",
        _BackupPreCheckResult.TargetNotFound: "Target not found",
        _BackupPreCheckResult.PermissionsError_TargetReadable_BackupNotWritable: "Permissions error: backup path not writable",
        _BackupPreCheckResult.PermissionsError_TargetNotReadable_BackupWritable: "Permissions error: target path or it's subdirectories not readable",
        _BackupPreCheckResult.PermissionsError_TargetNotReadable_BackupNotWritable:
            "Permissions error: target path or it's subdirectories not readable, backup path not writable"
    }

    @staticmethod
    def _backup_pre_check(item: BackupItem) -> _BackupPreCheckResult:
        if not item.TargetPath.exists():
            return _Backuper._BackupPreCheckResult.TargetNotFound

        is_target_read_allowed = _is_read_allowed(item.TargetPath)
        is_backup_write_allowed = _is_write_allowed(item.BackupPath)
        if is_target_read_allowed and not is_backup_write_allowed:
            return _Backuper._BackupPreCheckResult.PermissionsError_TargetReadable_BackupNotWritable
        if not is_target_read_allowed and is_backup_write_allowed:
            return _Backuper._BackupPreCheckResult.PermissionsError_TargetNotReadable_BackupWritable
        if not is_target_read_allowed and not is_backup_write_allowed:
            return _Backuper._BackupPreCheckResult.PermissionsError_TargetNotReadable_BackupNotWritable

        return _Backuper._BackupPreCheckResult.OK

    @staticmethod
    def _backup_process_files(item: BackupItem) -> _FileManipulationResult:
        try:
            if item.BackupPath.exists():
                _rm(item.BackupPath)

            if item.TargetPath.is_file():
                shutil.copy(item.TargetPath, item.BackupPath)
            else:
                shutil.copytree(item.TargetPath, item.BackupPath)

            return _FileManipulationResult(_FileManipulationStatus.OK, None)
        except Exception as e:
            return _FileManipulationResult(_FileManipulationStatus.Exception, e)

    @staticmethod
    def _backup_verify(item: BackupItem) -> _BackupVerificationResult:
        if not item.BackupPath.exists():
            return _Backuper._BackupVerificationResult.BackupNotFound

        return _Backuper._BackupVerificationResult.OK \
            if _SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath) \
            else _Backuper._BackupVerificationResult.BackupDifferentThanTarget

    @staticmethod
    def backup(item: BackupItem, is_dry_run: bool) -> ActionResult:
        pre_check_result = _Backuper._backup_pre_check(item)
        # noinspection DuplicatedCode
        if pre_check_result != _Backuper._BackupPreCheckResult.OK:
            return ActionResult(
                item.TargetPath,
                item.BackupPath,
                ActionStatus.Error, f"Pre-check failed [{_Backuper._pre_check_result_to_str_map[pre_check_result]}]"
            )

        if _SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath):
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.OK, None)

        if is_dry_run:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.DryRun, None)

        process_files_result = _Backuper._backup_process_files(item)
        if process_files_result.Status != _FileManipulationStatus.OK:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.Error, f"Process files failed [{process_files_result.Exception}]")

        verify_result = _Backuper._backup_verify(item)
        if verify_result != _Backuper._BackupVerificationResult.OK:
            return ActionResult(
                item.TargetPath,
                item.BackupPath,
                ActionStatus.Error,
                f"Verify failed [{_Backuper._verification_result_to_str_map[verify_result]}]"
            )

        return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.OK, None)


class _Restorer:
    @dataclass
    class RestoreItem:
        TargetPath: Path
        BackupPath: Path

    class _RestorePreCheckResult(Enum):
        OK = 1
        BackupNotFound = 2
        TargetParentNotFound = 3
        PermissionsError_TargetWritable_BackupNotReadable = 4
        PermissionsError_TargetNotWritable_BackupReadable = 5
        PermissionsError_TargetNotWritable_BackupNotReadable = 6

    class _RestoreVerificationResult(Enum):
        OK = 1
        OKButOldTargetBackupNotFound = 2
        TargetNotFound = 3
        BackupDifferentThanTarget = 4

    _pre_check_result_to_str_map = {
        _RestorePreCheckResult.OK: "OK",
        _RestorePreCheckResult.BackupNotFound: "Backup not found",
        _RestorePreCheckResult.TargetParentNotFound: "Target parent not found",
        _RestorePreCheckResult.PermissionsError_TargetWritable_BackupNotReadable:
            "Permissions error: backup path or it's subdirectories not readable",
        _RestorePreCheckResult.PermissionsError_TargetNotWritable_BackupReadable: "Permissions error: target path not writable",
        _RestorePreCheckResult.PermissionsError_TargetNotWritable_BackupNotReadable:
            "Permissions error: target path not writable, backup path or it's subdirectories not readable"
    }

    _verification_result_to_str_map = {
        _RestoreVerificationResult.OK: "OK",
        _RestoreVerificationResult.OKButOldTargetBackupNotFound:
            "OK, but old target backup not found (failed to backup old target or backup already was same as target, so no backup was made)",
        _RestoreVerificationResult.TargetNotFound: "Target not found",
        _RestoreVerificationResult.BackupDifferentThanTarget: "After restore, backup is different than target"
    }

    _old_target_backup_suffix = ".before_restore"

    @staticmethod
    def _restore_pre_check(item: RestoreItem) -> _RestorePreCheckResult:
        if not item.BackupPath.exists():
            return _Restorer._RestorePreCheckResult.BackupNotFound

        if not item.TargetPath.parent.exists():
            return _Restorer._RestorePreCheckResult.TargetParentNotFound

        is_target_write_allowed = _is_write_allowed(item.TargetPath)
        is_backup_read_allowed = _is_read_allowed(item.BackupPath)
        if is_target_write_allowed and not is_backup_read_allowed:
            return _Restorer._RestorePreCheckResult.PermissionsError_TargetWritable_BackupNotReadable
        if not is_target_write_allowed and is_backup_read_allowed:
            return _Restorer._RestorePreCheckResult.PermissionsError_TargetNotWritable_BackupReadable
        if not is_target_write_allowed and not is_backup_read_allowed:
            return _Restorer._RestorePreCheckResult.PermissionsError_TargetNotWritable_BackupNotReadable

        return _Restorer._RestorePreCheckResult.OK

    @staticmethod
    def _restore_process_files(item: RestoreItem) -> _FileManipulationResult:
        try:
            if item.TargetPath.exists():
                old_name = item.TargetPath.stem + _Restorer._old_target_backup_suffix + item.TargetPath.suffix
                if (item.TargetPath.parent / old_name).exists():
                    _rm(item.TargetPath.parent / old_name)
                os.rename(item.TargetPath, item.TargetPath.parent / old_name)

            if item.BackupPath.is_file():
                shutil.copy(item.BackupPath, item.TargetPath)
            else:
                shutil.copytree(item.BackupPath, item.TargetPath)
            return _FileManipulationResult(_FileManipulationStatus.OK, None)
        except Exception as e:
            return _FileManipulationResult(_FileManipulationStatus.Exception, e)

    @staticmethod
    def _restore_verify(item: RestoreItem) -> _RestoreVerificationResult:
        if not item.TargetPath.exists():
            return _Restorer._RestoreVerificationResult.TargetNotFound

        if not _SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath):
            return _Restorer._RestoreVerificationResult.BackupDifferentThanTarget

        old_target_copy = Path(item.TargetPath.parent / (item.TargetPath.stem + _Restorer._old_target_backup_suffix + item.TargetPath.suffix))
        if not old_target_copy.exists():
            return _Restorer._RestoreVerificationResult.OKButOldTargetBackupNotFound

        return _Restorer._RestoreVerificationResult.OK

    @staticmethod
    def restore(item: RestoreItem, is_dry_run: bool) -> ActionResult:
        pre_check_result = _Restorer._restore_pre_check(item)
        # noinspection DuplicatedCode
        if pre_check_result != _Restorer._RestorePreCheckResult.OK:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.Error, f"Pre-check failed [{pre_check_result.name}]")

        if _SimilarityVerifier.verify_same(item.TargetPath, item.BackupPath):
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.OK, None)

        if is_dry_run:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.DryRun, None)

        process_files_result = _Restorer._restore_process_files(item)
        if process_files_result.Status != _FileManipulationStatus.OK:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.Error, f"Process files failed [{process_files_result.Exception}]")

        verify_result = _Restorer._restore_verify(item)
        if verify_result != _Restorer._RestoreVerificationResult.OK:
            return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.Error, f"Verify failed [{verify_result.name}]")

        return ActionResult(item.TargetPath, item.BackupPath, ActionStatus.OK, None)


class _PyExecutor:
    @dataclass
    class ExecutePyResult:
        TargetPath: Path
        Status: ActionStatus
        ErrorText: str | None

    @staticmethod
    def execute_py(target_path: Path, py_file: Path, is_dry_run: bool) -> ExecutePyResult:
        assert py_file.exists(), f"Py file must exist [{py_file}]"

        if is_dry_run:
            return _PyExecutor.ExecutePyResult(target_path, ActionStatus.DryRun, None)

        try:
            subprocess.run(["python", py_file, target_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return _PyExecutor.ExecutePyResult(target_path, ActionStatus.OK, None)
        except subprocess.CalledProcessError as e:
            stdout = ''.join('>>>>' + line for line in e.stdout.decode('utf-8').splitlines(True))
            stderr = ''.join('>>>>' + line for line in e.stderr.decode('utf-8').splitlines(True))
            error_message = (
                    f"Command [{' '.join(e.cmd)}'] returned non-zero exit code [{e.returncode}]\n" +
                    (f"Standard Output:\n{stdout}\n" if stdout else "") +
                    (f"Standard Error:\n{stderr}\n" if stderr else "")
            )
            return _PyExecutor.ExecutePyResult(target_path, ActionStatus.Error, error_message)


class ConfigLoader:
    CONFIG_NAME = 'config.json'

    raw_config_target_path_json_key = "path"
    raw_config_post_restore_py_file_json_key = "post_restore_py_file"

    @dataclass
    class ConfigItem:
        TargetPath: Path
        PostRestorePyFile: Path | None

    @dataclass
    class ConfigLoadResult:
        class ConfigLoadStatus(Enum):
            AllOK = 1
            SomeFailed = 2
            AllFailed = 3
            ConfigDirNotExists = 4
            ConfigDirNotReadable = 5

        @dataclass
        class ConfigLoadError:
            ConfigPath: Path
            Error: Exception

        Status: ConfigLoadStatus
        Success: list[ImportedItem]
        Failed: list[ConfigLoadError]

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
    def load_configs(directory: Path) -> ConfigLoadResult:
        # noinspection PyPep8Naming
        statusType = ConfigLoader.ConfigLoadResult.ConfigLoadStatus
        # noinspection PyPep8Naming
        loadErrorType = ConfigLoader.ConfigLoadResult.ConfigLoadError

        if not directory.is_dir():
            return ConfigLoader.ConfigLoadResult(statusType.ConfigDirNotExists, [], [])
        if not _is_read_allowed(directory):
            return ConfigLoader.ConfigLoadResult(statusType.ConfigDirNotReadable, [], [])

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
        failed_configs: list[loadErrorType] = []
        for config_file in config_files:
            with open(config_file, 'r') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    failed_configs.append(loadErrorType(config_file, e))
                    continue
                loaded_configs.append(LoadedConfig(config_file, ConfigLoader._get_content_from_json(data)))

        imported_configs: list[ImportedItem] = []
        for loaded_config in loaded_configs:
            if isinstance(loaded_config.Content, list):
                imported_configs += [ImportedItem(
                    item.TargetPath,
                    loaded_config.ConfigPath.parent / item.TargetPath.name,
                    item.PyFile
                ) for item in loaded_config.Content]
                continue
            if isinstance(loaded_config.Content, ConfigLoader.ConfigItem):
                imported_configs.append(
                    ImportedItem(
                        loaded_config.Content.TargetPath,
                        loaded_config.ConfigPath.parent / loaded_config.Content.TargetPath.name,
                        loaded_config.Content.PostRestorePyFile
                    )
                )
                continue
            raise ValueError(f"Unknown config content type: {loaded_config.Content}")

        result_status: statusType = statusType.AllOK
        if failed_configs:
            result_status = statusType.SomeFailed
        if len(failed_configs) == len(config_files):
            result_status = statusType.AllFailed
        return ConfigLoader.ConfigLoadResult(result_status, imported_configs, failed_configs)


class _CLI:
    @staticmethod
    def _parse_args() -> tuple[Path, Mode]:
        parser = argparse.ArgumentParser(description='Backup/restore files and directories')
        parser.add_argument('mode', type=str, help='Mode: backup, restore', choices=['backup', 'restore'])
        parser.add_argument('--dir', type=str, help='Directory with config files', default='.')
        parser.add_argument('--dry-run', action='store_true', help='Dry run')
        args = parser.parse_args()

        return Path(args.dir), Mode(ActionType[args.mode.capitalize()], args.dry_run)

    @staticmethod
    def _create_config_load_summary(result: ConfigLoader.ConfigLoadResult) -> str:
        # noinspection PyPep8Naming
        configLoadStatusType = ConfigLoader.ConfigLoadResult.ConfigLoadStatus
        if result.Status is configLoadStatusType.ConfigDirNotExists:
            return 'Config directory not exists!'
        if result.Status is configLoadStatusType.ConfigDirNotReadable:
            return "Config directory or it's subdirectories not readable!"
        if result.Status is configLoadStatusType.AllFailed:
            return (f'Found {len(result.Failed)} configs\n' +
                    f'All failed to load!')
        if result.Status is configLoadStatusType.AllOK:
            return (f'Found {len(result.Success)} configs\n' +
                    f'All loaded successfully')
        if result.Status is configLoadStatusType.SomeFailed:
            errors = [f'\t{i + 1}. {error.ConfigPath} [{error.Error}]' for error, i in zip(result.Failed, range(len(result.Failed)))]
            return (f'Found {len(result.Success)} configs\n' +
                    f'Failed to load: {len(result.Failed)}' +
                    '\n'.join(errors) + '\n' +
                    f'Loaded successfully: {len(result.Success)}')
        raise ValueError(f"Unknown status: {result.Status}")

    @staticmethod
    def _create_run_summary(result: list[ActionResult]) -> str:
        success_results: list[ActionResult] = list(filter(lambda x: x.Status == ActionStatus.OK, result))
        failed_results: list[ActionResult] = list(filter(lambda x: x.Status == ActionStatus.Error, result))
        dry_run_results: list[ActionResult] = list(filter(lambda x: x.Status == ActionStatus.DryRun, result))
        if len(failed_results) == len(result):
            return ('Processing finished.\n' +
                    f'All {len(result)} failed!')
        if len(success_results) == len(result):
            return ('Processing finished.\n' +
                    f'All {len(result)} successful!')
        if len(dry_run_results) == len(result):
            return ('Processing finished.\n' +
                    f'All {len(result)} dry run, no errors.')
        errors = [
            (f'>>>>{i + 1}.\n' +
             f'>>>>Target path [{error.TargetPath}]\n' +
             f'>>>>Backup path [{error.BackupPath}]\n' +
             f'>>>>Error: {error.ErrorText}')
            for error, i in zip(failed_results, range(len(failed_results)))
        ]
        return ('Processing finished.\n' +
                (f'Success: {len(success_results)}\n' if any(success_results) else '') +
                (f'Dry run: {len(dry_run_results)}\n' if any(dry_run_results) else '') +
                (f'Failed: {len(failed_results)}\n' + '\n'.join(errors) if any(failed_results) else ''))

    @staticmethod
    def cli_entry_point() -> None:
        directory, mode = _CLI._parse_args()
        directory = directory.resolve()

        print(
            'Starting...',
            f'Directory: {directory}',
            f'Mode: {mode.ActionType.name}',
            'Dry run' if mode.IsDryRun else '',
            sep='\n'
        )

        config_load_result = ConfigLoader.load_configs(directory)
        print(_CLI._create_config_load_summary(config_load_result))

        # noinspection PyPep8Naming
        configLoadStatusType = ConfigLoader.ConfigLoadResult.ConfigLoadStatus
        if config_load_result.Status not in [configLoadStatusType.AllOK, configLoadStatusType.SomeFailed]:
            print("Cannot continue, exiting...")
            exit(1)

        print('\nStarting processing...')
        results = run(mode, config_load_result.Success)

        print(_CLI._create_run_summary(results))
        print('Finished')
        exit(0)


if __name__ == "__main__":
    _CLI.cli_entry_point()
