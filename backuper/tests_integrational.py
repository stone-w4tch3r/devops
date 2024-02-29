import unittest
import shutil
from backuper import backup, BackupItem, BackupPreCheckResult, ImportedItem, restore, RestoreResult, RestoreItem
from pathlib import Path
import os

TESTING_DIR = './testing_dir'
TARGET_PATH = f'{TESTING_DIR}/item_to_backup'
BACKUP_PATH = f'{TESTING_DIR}/backup'


def rm_test_files():
    for root, dirs, files in os.walk(TESTING_DIR):
        for file in files:
            os.remove(f'{root}/{file}')
        for directory in dirs:
            shutil.rmtree(f'{root}/{directory}')


# noinspection DuplicatedCode
class TestBackup(unittest.TestCase):
    backup_item = BackupItem(Path(TARGET_PATH), Path(BACKUP_PATH))

    def tearDown(self):
        rm_test_files()

    def setUp(self):
        rm_test_files()

    def test_target_not_exists_then_fail(self):
        # arrange
        self.assertFalse(os.path.exists(TARGET_PATH))

        # act
        result = backup(self.backup_item)

        # assert
        self.assertEqual(result, BackupPreCheckResult.TargetNotFound)
        self.assertFalse(os.path.exists(BACKUP_PATH))

    def test_target_exists_then_ok(self):
        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)

        # act
        result = backup(self.backup_item)

        # assert
        self.assertEqual(result, BackupPreCheckResult.OK)
        self.assertTrue(os.path.exists(BACKUP_PATH))

    def test_target_is_file_then_ok(self):
        content = 'test'

        # arrange
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(content)

        # act
        result = backup(self.backup_item)

        # assert
        self.assertEqual(result, BackupPreCheckResult.OK)
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
        result = backup(self.backup_item)

        # assert
        self.assertEqual(result, BackupPreCheckResult.OK)
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
        backup(self.backup_item)  # create initial backup

        # change the content of the target
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(new_content)

        # act
        result = backup(self.backup_item)  # create a new backup

        # assert
        self.assertEqual(result, BackupPreCheckResult.OK)
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
        backup(self.backup_item)  # create initial backup

        # change the content of the target
        with open(f'{TARGET_PATH}/file1', 'w') as f:
            f.write(new_content)
        with open(f'{TARGET_PATH}/file2', 'w') as f:
            f.write(new_content)

        # act
        result = backup(self.backup_item)

        # assert
        self.assertEqual(result, BackupPreCheckResult.OK)
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}'))
        self.assertTrue(os.path.isdir(f'{BACKUP_PATH}'))
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file1'))
        self.assertTrue(os.path.exists(f'{BACKUP_PATH}/file2'))
        with open(f'{BACKUP_PATH}/file1', 'r') as f:
            self.assertEqual(f.read(), new_content)
        with open(f'{BACKUP_PATH}/file2', 'r') as f:
            self.assertEqual(f.read(), new_content)


# noinspection DuplicatedCode
class TestRestore(unittest.TestCase):
    restore_item = RestoreItem(Path(TARGET_PATH), Path(BACKUP_PATH), None)

    def tearDown(self):
        rm_test_files()

    def setUp(self):
        rm_test_files()

    def test_backup_not_exists_then_fail(self):
        # arrange
        self.assertFalse(os.path.exists(BACKUP_PATH))

        # act
        result = restore(self.restore_item)

        # assert
        self.assertEqual(result, RestoreResult.BackupNotFound)

    def test_target_parent_not_exists_then_fail(self):
        # arrange
        target_path = f'{TESTING_DIR}/not_exists/item_to_backup'
        restore_item = RestoreItem(Path(target_path), Path(BACKUP_PATH), None)
        os.makedirs(BACKUP_PATH, exist_ok=True)
        self.assertFalse(os.path.exists(target_path))

        # act
        result = restore(restore_item)

        # assert
        self.assertEqual(result, RestoreResult.TargetParentNotFound)

    def test_successful_restore_for_file_then_success(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)

        # act
        result = restore(self.restore_item)

        # assert
        self.assertEqual(result, RestoreResult.OK)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.isfile(TARGET_PATH))
        with open(TARGET_PATH, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_successful_restore_for_directory_then_success(self):
        # arrange
        content = 'test'
        os.makedirs(BACKUP_PATH, exist_ok=True)
        with open(f'{BACKUP_PATH}/file1', 'w') as f:
            f.write(content)

        # act
        result = restore(self.restore_item)

        # assert
        self.assertEqual(result, RestoreResult.OK)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.isdir(TARGET_PATH))
        self.assertTrue(os.path.exists(f'{TARGET_PATH}/file1'))
        with open(f'{TARGET_PATH}/file1', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_post_restore_error_then_fail(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)
        post_restore_py_file = Path(TESTING_DIR) / 'post_restore.py'
        with open(post_restore_py_file, 'w') as f:
            f.write("import sys; sys.exit(1)")
        restore_item = RestoreItem(Path(TARGET_PATH), Path(BACKUP_PATH), post_restore_py_file)

        # act
        result = restore(restore_item)

        # assert
        self.assertEqual(result, RestoreResult.PostRestoreError)

    def test_post_restore_called_then_side_effects_present(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)
        post_restore_py_file = Path(TARGET_PATH).parent / "post_restore.py"
        post_restore_output_file = Path(TARGET_PATH).parent / "post_restore_output.txt"
        with open(post_restore_py_file, 'w') as f:
            f.write(f"with open('{post_restore_output_file}', 'w') as f: f.write('post_restore was here')")
        restore_item = RestoreItem(Path(TARGET_PATH), Path(BACKUP_PATH), post_restore_py_file)

        # act
        result = restore(restore_item)

        # assert
        self.assertEqual(result, RestoreResult.OK)
        with open(post_restore_output_file, 'r') as f:
            self.assertEqual(f.read(), 'post_restore was here')

    def test_old_target_renamed_and_then_removed(self):
        # arrange
        content = 'test'
        content_new = 'new test'
        old_target_path = f'{TARGET_PATH}.old_restored'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)
        with open(TARGET_PATH, 'w') as f:
            f.write(content)

        # act 1
        result = restore(self.restore_item)
        self.assertEqual(result, RestoreResult.OK)
        self.assertTrue(os.path.exists(old_target_path))
        with open(old_target_path, 'r') as f:
            self.assertEqual(f.read(), content)

        # act 2
        with open(TARGET_PATH, 'w') as f:
            f.write(content_new)
        result = restore(self.restore_item)
        self.assertEqual(result, RestoreResult.OK)
        self.assertTrue(os.path.exists(old_target_path))
        with open(old_target_path, 'r') as f:
            self.assertEqual(f.read(), content_new)

        # assert
        self.assertEqual(result, RestoreResult.OK)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.exists(old_target_path))


if __name__ == '__main__':
    unittest.main()
