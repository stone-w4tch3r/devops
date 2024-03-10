import os
import re
import shutil
import unittest
from pathlib import Path

from backup_tool import run, Mode, ActionType, ImportedItem, ActionStatus

TESTING_DIR = Path('./testing_dir').expanduser().resolve()
TARGET_PATH = Path(TESTING_DIR / 'item_to_backup')
BACKUP_PATH = Path(TESTING_DIR / 'backup')


def rm_test_files():
    for root, dirs, files in os.walk(TESTING_DIR):
        for file in files:
            os.remove(f'{root}/{file}')
        for directory in dirs:
            shutil.rmtree(f'{root}/{directory}')


# noinspection DuplicatedCode
class TestBackup(unittest.TestCase):
    backup_item = ImportedItem(TARGET_PATH, BACKUP_PATH, None)
    mode = Mode(ActionType.Backup, False)

    def tearDown(self):
        rm_test_files()

    def setUp(self):
        rm_test_files()

    def test_target_not_exists_then_fail(self):
        # arrange
        self.assertFalse(os.path.exists(TARGET_PATH))

        # act
        result = run(self.mode, [self.backup_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.Error)
        self.assertRegex(result[0].ErrorText, re.compile(".*target.*not.*found.*", re.IGNORECASE))
        self.assertFalse(os.path.exists(BACKUP_PATH))

    def test_target_exists_then_ok(self):
        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)

        # act
        result = run(self.mode, [self.backup_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(BACKUP_PATH))

    def test_target_is_file_then_ok(self):
        content = 'test'

        # arrange
        with open(f'{TARGET_PATH}', 'w') as f:
            f.write(content)

        # act
        result = run(self.mode, [self.backup_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(BACKUP_PATH))
        self.assertTrue(os.path.isfile(BACKUP_PATH))
        with open(BACKUP_PATH, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_backup_target_is_directory_then_ok(self):
        content = 'test'

        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)
        with open(TARGET_PATH / 'file1', 'w') as f:
            f.write(content)

        # act
        result = run(self.mode, [self.backup_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(BACKUP_PATH))
        self.assertTrue(os.path.isdir(BACKUP_PATH))
        self.assertTrue(os.path.exists(BACKUP_PATH / 'file1'))
        with open(BACKUP_PATH / 'file1', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_backup_exists_then_overwrite_file(self):
        content = 'test'
        new_content = 'new test'

        # arrange
        with open(TARGET_PATH, 'w') as f:
            f.write(content)
        run(self.mode, [self.backup_item])  # create initial backup
        with open(TARGET_PATH, 'w') as f:
            f.write(new_content)

        # act
        result = run(self.mode, [self.backup_item])  # create a new backup

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(BACKUP_PATH))
        self.assertTrue(os.path.isfile(BACKUP_PATH))
        with open(BACKUP_PATH, 'r') as f:
            self.assertEqual(f.read(), new_content)

    def test_backup_exists_then_overwrite_dir(self):
        content = 'test'
        new_content = 'new test'

        # arrange
        os.makedirs(TARGET_PATH, exist_ok=True)
        with open(TARGET_PATH / 'file1', 'w') as f:
            f.write(content)
        #         backup_process_files(self.backup_item)  # create initial backup
        run(self.mode, [self.backup_item])  # create initial backup

        # change the content of the target
        with open(TARGET_PATH / 'file1', 'w') as f:
            f.write(new_content)
        with open(TARGET_PATH / 'file2', 'w') as f:
            f.write(new_content)

        # act
        result = run(self.mode, [self.backup_item])  # create a new backup

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.backup_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.backup_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(BACKUP_PATH))
        self.assertTrue(os.path.isdir(BACKUP_PATH))
        self.assertTrue(os.path.exists(BACKUP_PATH / 'file1'))
        self.assertTrue(os.path.exists(BACKUP_PATH / 'file2'))
        with open(BACKUP_PATH / 'file1', 'r') as f:
            self.assertEqual(f.read(), new_content)
        with open(BACKUP_PATH / 'file2', 'r') as f:
            self.assertEqual(f.read(), new_content)


# noinspection DuplicatedCode
class TestRestore(unittest.TestCase):
    restore_item = ImportedItem(TARGET_PATH, BACKUP_PATH, None)
    mode = Mode(ActionType.Restore, False)

    def tearDown(self):
        rm_test_files()

    def setUp(self):
        rm_test_files()

    def test_backup_not_exists_then_fail(self):
        # arrange
        self.assertFalse(os.path.exists(BACKUP_PATH))

        # act
        result = run(self.mode, [self.restore_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.Error)
        self.assertRegex(result[0].ErrorText, re.compile(".*backup.*not.*found.*", re.IGNORECASE))
        self.assertFalse(os.path.exists(TARGET_PATH))

    def test_target_parent_not_exists_then_fail(self):
        # arrange
        target_path = TESTING_DIR / 'not_exists' / 'item_to_backup'
        restore_item = ImportedItem(target_path, BACKUP_PATH, None)
        os.makedirs(BACKUP_PATH, exist_ok=True)
        self.assertFalse(os.path.exists(target_path))

        # act
        result = run(self.mode, [restore_item])

        # assert
        # self.assertEqual(result, RestoreResult.TargetParentNotFound)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.Error)
        self.assertRegex(result[0].ErrorText, re.compile(".*parent.*not.*found.*", re.IGNORECASE))

    def test_successful_restore_for_file_then_success(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)

        # act
        result = run(self.mode, [self.restore_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.isfile(TARGET_PATH))
        with open(TARGET_PATH, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_successful_restore_for_directory_then_success(self):
        # arrange
        content = 'test'
        os.makedirs(BACKUP_PATH, exist_ok=True)
        with open(BACKUP_PATH / 'file1', 'w') as f:
            f.write(content)

        # act
        result = run(self.mode, [self.restore_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.isdir(TARGET_PATH))
        self.assertTrue(os.path.exists(TARGET_PATH / 'file1'))
        with open(TARGET_PATH / 'file1', 'r') as f:
            self.assertEqual(f.read(), content)

    def test_post_restore_error_then_fail(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)
        post_restore_py_file = Path(TESTING_DIR) / 'post_restore.py'
        with open(post_restore_py_file, 'w') as f:
            f.write("import sys; print('start'); sys.stderr.write('error'); sys.exit(1)")
        restore_item = ImportedItem(TARGET_PATH, BACKUP_PATH, post_restore_py_file)

        # act
        result = run(self.mode, [restore_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.Error)
        self.assertRegex(result[0].ErrorText, re.compile(".*exit.*code.*1.*", re.IGNORECASE))

    def test_post_restore_called_then_side_effects_present(self):
        # arrange
        content = 'test'
        with open(BACKUP_PATH, 'w') as f:
            f.write(content)
        post_restore_py_file = TARGET_PATH.parent / "post_restore.py"
        post_restore_output_file = TARGET_PATH.parent / "post_restore_output.txt"
        with open(post_restore_py_file, 'w') as f:
            f.write(f"with open('{post_restore_output_file}', 'w') as f: f.write('post_restore was here')")
        restore_item = ImportedItem(TARGET_PATH, BACKUP_PATH, post_restore_py_file)

        # act
        result = run(self.mode, [restore_item])

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        with open(post_restore_output_file, 'r') as f:
            self.assertEqual(f.read(), 'post_restore was here')

    def test_old_target_renamed_and_then_removed(self):
        # arrange
        content_1 = 'test'
        content_2 = 'new test'
        content_3 = 'new new test'
        old_target_path = TARGET_PATH.parent / (TARGET_PATH.stem + '.before_restore' + TARGET_PATH.suffix)
        with open(BACKUP_PATH, 'w') as f:
            f.write(content_2)
        with open(TARGET_PATH, 'w') as f:
            f.write(content_1)

        # act 1
        result = run(self.mode, [self.restore_item])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertTrue(os.path.exists(old_target_path))
        with open(old_target_path, 'r') as f:
            self.assertEqual(f.read(), content_1)

        # act 2
        with open(TARGET_PATH, 'w') as f:
            f.write(content_3)
        result = run(self.mode, [self.restore_item])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertTrue(os.path.exists(old_target_path))
        with open(old_target_path, 'r') as f:
            self.assertEqual(f.read(), content_3)

        # assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].TargetPath, self.restore_item.TargetPath)
        self.assertEqual(result[0].BackupPath, self.restore_item.BackupPath)
        self.assertEqual(result[0].Status, ActionStatus.OK)
        self.assertIsNone(result[0].ErrorText)
        self.assertTrue(os.path.exists(TARGET_PATH))
        self.assertTrue(os.path.exists(old_target_path))


if __name__ == '__main__':
    unittest.main()
