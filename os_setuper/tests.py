import subprocess
import unittest

from vbox_vm_recreate import recreate as recreate_vm


def _run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


basic = f"pyinfra test_inventory.py playbooks/all.py"


class TestAppsExample(unittest.TestCase):

    def setUp(self):
        recreate_vm()

    def test_main(self):
        _run("pyinfra apps_example.py")
