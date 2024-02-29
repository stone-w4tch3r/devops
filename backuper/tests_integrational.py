import unittest
import shutil
from backuper import backup, ToBackupItem, BackupResult, BackupResultType
from pathlib import Path
import os

TARGET_PATH = './testing_dir/item_to_backup'
BACKUP_PATH = './testing_dir/backup'


class TestBackup(unittest.TestCase):
    backup_result_target_not_found = [
        BackupResult(TargetPath=Path(TARGET_PATH), BackupPath=Path(BACKUP_PATH), Result=BackupResultType.TargetNotFound)
    ]
    backup_result_ok = [
        BackupResult(TargetPath=Path(TARGET_PATH), BackupPath=Path(BACKUP_PATH), Result=BackupResultType.OK)
    ]
    config_items = [
        ToBackupItem(TargetPath=Path(TARGET_PATH), BackupPath=Path(BACKUP_PATH))
    ]

    @staticmethod
    def rm_test_files():
        if os.path.exists(TARGET_PATH):
            if os.path.isfile(TARGET_PATH):
                os.remove(TARGET_PATH)
            else:
                shutil.rmtree(TARGET_PATH)
        if os.path.exists(BACKUP_PATH):
            if os.path.isfile(BACKUP_PATH):
                os.remove(BACKUP_PATH)
            else:
                shutil.rmtree(BACKUP_PATH)

    def tearDown(self):
        self.rm_test_files()

    def setUp(self):
        self.rm_test_files()

    def test_target_not_exists_then_fail(self):
        # arrange
        self.assertFalse(os.path.exists(TARGET_PATH))

        # act
        result = backup(self.config_items)

        # assert
        self.assertEqual(result, self.backup_result_target_not_found)
        self.assertFalse(os.path.exists(BACKUP_PATH))

    def test_target_exists_then_ok(self):
        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)

        # act
        result = backup(self.config_items)

        # assert
        self.assertEqual(result, self.backup_result_ok)
        self.assertTrue(os.path.exists(BACKUP_PATH))

    def test_target_is_file_then_ok(self):
        content = 'test'

        # arrange
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(content)

        # act
        result = backup(self.config_items)

        # assert
        self.assertEqual(result, self.backup_result_ok)
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}'))
        self.assertTrue(os.path.isfile(f'{BACKUP_PATH}'))
        with open(f'{BACKUP_PATH}', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_backup_target_is_directory_then_ok(self):
        content = 'test'

        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)
        with open(f'{TARGET_PATH}/file1', 'w') as f:
            f.write(content)
        with open(f'{TARGET_PATH}/file2', 'w') as f:
            f.write(content)

        # act
        result = backup(self.config_items)

        # assert
        self.assertEqual(result, self.backup_result_ok)
        self.assertTrue(os.path.exists(BACKUP_PATH))
        self.assertTrue(os.path.isdir(BACKUP_PATH))
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file1'))
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file2'))
        with open(f'{BACKUP_PATH}/file1', 'r') as f:
            self.assertEqual(f.read(), content)
        with open(f'{BACKUP_PATH}/file2', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_backup_exists_then_overwrite_file(self):
        content = 'test'
        new_content = 'new test'

        # arrange
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(content)
        backup(self.config_items)  # create initial backup

        # change the content of the target
        # noinspection DuplicatedCode
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(new_content)

        # act
        result = backup(self.config_items)  # create a new backup

        # assert
        self.assertEqual(result, self.backup_result_ok)
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}'))
        self.assertTrue(os.path.isfile(f'{BACKUP_PATH}'))
        with open(f'{BACKUP_PATH}', 'r') as f:
            self.assertEqual(f.read(), new_content)

    def test_backup_exists_then_overwrite_dir(self):
        content = 'test'
        new_content = 'new test'

        # arrange
        os.makedirs(f'{TARGET_PATH}', exist_ok=True)
        with open(f'{TARGET_PATH}/file1', 'w') as f:
            f.write(content)
        backup(self.config_items)  # create initial backup

        # change the content of the target
        with open(f'{TARGET_PATH}/file1', 'w') as f:
            f.write(new_content)
        with open(f'{TARGET_PATH}/file2', 'w') as f:
            f.write(new_content)

        # act
        result = backup(self.config_items)

        # assert
        self.assertEqual(result, self.backup_result_ok)
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}'))
        self.assertTrue(os.path.isdir(f'{BACKUP_PATH}'))
        # noinspection DuplicatedCode
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file1'))
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file2'))
        with open(f'{BACKUP_PATH}/file1', 'r') as f:
            self.assertEqual(f.read(), new_content)
        with open(f'{BACKUP_PATH}/file2', 'r') as f:
            self.assertEqual(f.read(), new_content)


if __name__ == '__main__':
    unittest.main()
