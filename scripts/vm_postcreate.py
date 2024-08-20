#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path


def run(command: str) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


KEYS_DIR_PATH = Path(__file__).resolve().parent / "../pyinfra_manager/keys"


def main(vm_name: str, vm_ip: str, keys_dir: Path = KEYS_DIR_PATH):
    known_hosts = Path("~/.ssh/known_hosts").expanduser()

    print("Performing post-creation tasks...")

    # update /etc/hosts
    run(f"sudo sed -i '/{vm_name}/d' /etc/hosts")  # /PATTERN/d - delete line with PATTERN
    run(f"echo '{vm_ip} {vm_name}' | sudo tee -a /etc/hosts")

    # remove identity from known_hosts
    run(f"ssh-keygen -f {known_hosts} -R {vm_ip}")
    run(f"ssh-keygen -f {known_hosts} -R {vm_name}")

    # append identity to known_hosts
    with open(known_hosts, "a") as f:
        f.write(run(f"ssh-keyscan '{vm_name}'"))

    # remove old keys
    for key in os.listdir(keys_dir):
        if os.path.isfile(key) and vm_name in key:
            os.remove(key)

    print("Post-creation tasks completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Perform post-creation tasks for a VirtualBox/multipass/other VM.

        This script automates several tasks after a VM has been created:
        1. Updates /etc/hosts with the VM's IP and hostname.
        2. Removes old SSH known hosts entries for the VM's IP and hostname.
        3. Adds a new SSH known hosts entry for the VM.
        4. Removes old SSH keys associated with the VM.

        The script uses system commands and file operations to perform these tasks.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vm-name", type=str, required=True)
    parser.add_argument("--vm-ip", type=str, required=True)
    parser.add_argument("--keys-dir-path", type=str, default=KEYS_DIR_PATH)
    args = parser.parse_args()
    main(args.vm_name, args.vm_ip, Path(args.keys_dir_path).expanduser().resolve())
