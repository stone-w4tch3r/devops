import subprocess
import unittest
from pathlib import Path

from vbox_recreate import recreate as recreate_vm


def _run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


_test_inventory = Path(__file__).parent / "test_inventory.py"
_test_task = Path(__file__).parent / "apps_example.py"
_basic = f"pyinfra {_test_inventory} {_test_task}"


class TestAppsExample(unittest.TestCase):

    def setUp(self):
        recreate_vm()

    def test_main(self):
        _run(f"pyinfra {_test_inventory} {_test_task}")
