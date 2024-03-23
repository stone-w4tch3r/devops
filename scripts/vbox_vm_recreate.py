#!/usr/bin/env python3

import argparse
import os
import subprocess
import time
from pathlib import Path

from vm_postcreate import main as post_create


def _run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def _create_network_if_not_exists(network_name: str, network_ip: str):
    if network_name not in _run("VBoxManage list hostonlyifs"):
        _run("VBoxManage hostonlyif create")
        _run(f"VBoxManage hostonlyif ipconfig {network_name} --ip {network_ip} --netmask 255.255.255.0")


TMPDIR = os.getenv('TMPDIR', '/tmp')
DEFAULT_OVA_FILE = "~/VMs/jammy-server-cloudimg-amd64.ova"
DEFAULT_VM_NAME = "vbox-primary"
DEFAULT_NETWORK_NAME = "vboxnet0"
DEFAULT_NETWORK_IP = "192.168.56.1"
DEFAULT_VM_IP = "192.168.56.101"
DEFAULT_CPU_COUNT = 2
DEFAULT_RAM_IN_MB = 2048


# todo: fix display type (see vm settings)
def recreate(
    ova_file_path: str = DEFAULT_OVA_FILE,
    vm_name: str = DEFAULT_VM_NAME,
    cpu_count: int = DEFAULT_CPU_COUNT,
    ram_in_mb: int = DEFAULT_RAM_IN_MB
):
    ova_file = Path(ova_file_path).expanduser()
    seed_iso = Path(TMPDIR) / "ubuntu-seed.iso"
    cloud_init = Path(__file__).parent / "vbox-vm-cloud-init.yml"

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print("Welcome to the VM starter script")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    if vm_name in _run("VBoxManage list vms"):
        print("VM already exists. Deleting it...")
        _run(f"VBoxManage controlvm {vm_name} poweroff")
        _run(f"VBoxManage unregistervm {vm_name} --delete")
        print("VM deleted")

    print("Ensuring network exists...")
    _create_network_if_not_exists(DEFAULT_NETWORK_NAME, DEFAULT_NETWORK_IP)

    print("Creating VM...")
    _run(f"cloud-localds {seed_iso} {cloud_init}")
    _run(f"VBoxManage import {ova_file} --vsys 0 --vmname {vm_name}")
    _run(f"VBoxManage storageattach {vm_name} --storagectl IDE --port 1 --device 0 --type dvddrive --medium {seed_iso}")
    _run(f"VBoxManage modifyvm {vm_name} --cpus {cpu_count} --memory {ram_in_mb}")
    _run(f"VBoxManage modifyvm {vm_name} --nic1 hostonly --hostonlyadapter1 {DEFAULT_NETWORK_NAME}")
    _run(f"VBoxManage startvm {vm_name} --type headless")

    time.sleep(30)

    info = _run(f"VBoxManage showvminfo {vm_name}")
    vm_state = info.split(':')[-1].strip()
    vm_os = info.split(':')[-2].strip()
    vm_ip = DEFAULT_VM_IP  # todo: support hostonly ip assignment

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--ova-file", type=str, default=DEFAULT_OVA_FILE)
    parser.add_argument("--vm-name", type=str, default=DEFAULT_VM_NAME)
    parser.add_argument("--cpu-count", type=int, default=DEFAULT_CPU_COUNT)
    parser.add_argument("--ram-in-mb", type=int, default=DEFAULT_RAM_IN_MB)
    args = parser.parse_args()
    recreate(args.ova_file, args.vm_name, args.cpu_count, args.ram_in_mb)
