#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Callable

from vm_postcreate import main as post_create


def run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def get_vm_ip(vm_name: str) -> str:
    is_ip_valid: Callable = lambda ip_to_match: bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_to_match))
    get_ip: Callable = lambda: run(f"VBoxManage guestproperty get {vm_name} '/VirtualBox/GuestInfo/Net/0/V4/IP'").split()[-1]

    ip = get_ip()
    if not is_ip_valid(ip):
        time.sleep(10)
        ip = get_ip()

    if not is_ip_valid(ip):
        print("VM IP not found. Try it yourself")
        exit(1)

    return ip


TMPDIR = os.getenv('TMPDIR', '/tmp')
DEFAULT_OVA_FILE = "~/VMs/jammy-server-cloudimg-amd64.ova"
DEFAULT_VM_NAME = "vbox-primary"
DEFAULT_CPU_COUNT = 2
DEFAULT_RAM_IN_MB = 2048


def recreate(
    ova_file_path: str = DEFAULT_OVA_FILE,
    vm_name: str = DEFAULT_VM_NAME,
    cpu_count: int = DEFAULT_CPU_COUNT,
    ram_in_mb: int = DEFAULT_RAM_IN_MB
) -> str:
    ova_file = Path(ova_file_path).expanduser()
    seed_iso = Path(TMPDIR) / "ubuntu-seed.iso"
    cloud_init = "./vbox-vm-cloud-init.yml"

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print("Welcome to the VM starter script")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    if vm_name in run("VBoxManage list vms"):
        print("VM already exists. Deleting it...")
        run(f"VBoxManage controlvm {vm_name} poweroff")
        run(f"VBoxManage unregistervm {vm_name} --delete")
        print("VM deleted")

    print("Creating VM...")
    run(f"cloud-localds {seed_iso} {cloud_init}")
    run(f"VBoxManage import {ova_file} --vsys 0 --vmname {vm_name}")
    run(f"VBoxManage storageattach {vm_name} --storagectl IDE --port 1 --device 0 --type dvddrive --medium {seed_iso}")
    run(f"VBoxManage modifyvm {vm_name} --cpus {cpu_count} --memory {ram_in_mb}")
    run(f"VBoxManage startvm {vm_name} --type headless")

    time.sleep(45)

    info = run(f"VBoxManage showvminfo {vm_name}")
    vm_state = info.split(':')[-1].strip()
    vm_os = info.split(':')[-2].strip()
    vm_ip = get_vm_ip(vm_name)

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
