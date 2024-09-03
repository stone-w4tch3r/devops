#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from typing import Callable

from vm_postcreate import main as post_create


def _run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def _validate_positive_int(value: str) -> str:
    if isinstance(value, int) and value > 0:
        return value
    raise argparse.ArgumentTypeError(f"{value} is not a positive integer")


def _validate_ova_file(value: str) -> str:
    path = Path(value).expanduser()
    if not path.exists() or not path.is_file():
        raise argparse.ArgumentTypeError(f"{value} is not a valid file")
    if path.suffix.lower() != '.ova':
        raise argparse.ArgumentTypeError(f"{value} is not an OVA file")
    return str(path)


def _validate_vm_name(value: str) -> str:
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise argparse.ArgumentTypeError(f"{value} is not a valid VM name. Use only alphanumeric characters, underscores, and hyphens.")
    return value


def _get_vm_ip(vm_name: str) -> str:
    is_ip_valid: Callable = lambda ip_to_match: bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_to_match))
    get_ip: Callable = lambda: _run(f"VBoxManage guestproperty get {vm_name} '/VirtualBox/GuestInfo/Net/0/V4/IP'").split()[-1]

    timeout = 80
    step = 20
    for seconds_passed in range(0, timeout, step):
        ip = get_ip()
        if is_ip_valid(ip):
            break
        time.sleep(step)
        print(f"VM IP is not yet available. Waiting more... ({seconds_passed + step}/{timeout} s)")
    else:
        print("VM IP not found. Try it yourself")
        exit(1)

    return ip


DEFAULT_OVA_FILE = "~/VMs/jammy-server-cloudimg-amd64.ova"
DEFAULT_VM_NAME = "vbox-primary"
DEFAULT_CPU_COUNT = 2
DEFAULT_RAM_IN_MB = 2048

CLOUD_INIT = Path(__file__).parent.resolve() / "vbox-cloud-init.yml"
SEED_ISO = Path(os.getenv('TMPDIR', '/tmp')) / "ubuntu-seed.iso"


def recreate(
    ova_file_path: str = DEFAULT_OVA_FILE,
    vm_name: str = DEFAULT_VM_NAME,
    cpu_count: int = DEFAULT_CPU_COUNT,
    ram_in_mb: int = DEFAULT_RAM_IN_MB
):
    ova_file = Path(ova_file_path).expanduser()

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print("Welcome to the VM starter script")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    if vm_name in _run("VBoxManage list vms"):
        print("VM already exists. Deleting it...")
        with suppress(subprocess.CalledProcessError):
            _run(f"VBoxManage controlvm {vm_name} poweroff")
        _run(f"VBoxManage unregistervm {vm_name} --delete")
        print("VM deleted")

    print("Creating VM...")
    _run(f"cloud-localds {SEED_ISO} {CLOUD_INIT}")
    _run(f"VBoxManage import {ova_file} --vsys 0 --vmname {vm_name}")
    _run(f"VBoxManage storageattach {vm_name} --storagectl IDE --port 1 --device 0 --type dvddrive --medium {SEED_ISO}")
    _run(f"VBoxManage modifyvm {vm_name} --cpus {cpu_count} --memory {ram_in_mb}")
    _run(f"VBoxManage modifyvm {vm_name} --graphicscontroller vmsvga")
    _run(f"VBoxManage startvm {vm_name} --type headless")

    info = _run(f"VBoxManage showvminfo {vm_name}")
    vm_state = info.split(':')[-1].strip()
    vm_os = info.split(':')[-2].strip()
    vm_ip = _get_vm_ip(vm_name)

    post_create(vm_name, vm_ip)

    print()
    print("VM started")
    print(f"VM Name: {vm_name}")
    print(f"VM State: {vm_state}")
    print(f"VM OS: {vm_os}")
    print(f"VM IP: {vm_ip}")
    print()
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print("Done")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Recreate a VirtualBox VM from an OVA file.

        This script automates the process of creating or recreating a VirtualBox VM:
        1. If a VM with the specified name already exists, it is deleted.
        2. A cloud-init ISO is created with the 'vbox-cloud-init.yml' file.
        3. The new VM is imported from the specified OVA file.
        4. The cloud-init ISO is attached to the VM.
        5. VM settings (CPU, RAM, graphics controller) are configured.
        6. The VM is started in headless mode.
        7. The script waits for the VM to obtain an IP address.
        8. Post-creation tasks are performed using the vm_postcreate.py script.

        The script uses VBoxManage CLI.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--ova-file",
        type=_validate_ova_file,
        default=DEFAULT_OVA_FILE,
        help=f"Path to the OVA file (default: {DEFAULT_OVA_FILE})"
    )
    parser.add_argument(
        "--vm-name",
        type=_validate_vm_name,
        default=DEFAULT_VM_NAME,
        help=f"Name of the VM (default: {DEFAULT_VM_NAME})"
    )
    parser.add_argument(
        "--cpu-count",
        type=_validate_positive_int,
        default=DEFAULT_CPU_COUNT,
        help=f"Number of CPUs for the VM (default: {DEFAULT_CPU_COUNT})"
    )
    parser.add_argument(
        "--ram-in-mb",
        type=_validate_positive_int,
        default=DEFAULT_RAM_IN_MB,
        help=f"Amount of RAM in MB for the VM (default: {DEFAULT_RAM_IN_MB})"
    )
    args = parser.parse_args()
    recreate(args.ova_file, args.vm_name, args.cpu_count, args.ram_in_mb)
