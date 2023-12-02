#!/usr/bin/env python3

import os
import subprocess


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


TARGET_NAME = "primary.multipass"
RECREATE_COMMAND = "~/Projects/devops/scripts/multipass_recreate_primary.py"
DEFAULT_DISTRO = "jammy"

print("++++++++++++++++++++++++++++++++")
print("recreating deploy environment")
print("++++++++++++++++++++++++++++++++")

print("cleaning up")
keys = [f"keys/{TARGET_NAME}.ssh-key", f"keys/{TARGET_NAME}.ssh-key.pub"]
for key in keys:
    if os.path.isfile(key):
        os.remove(key)

print("recreating vm:")
print()
distro = DEFAULT_DISTRO if len(os.sys.argv) <= 1 else os.sys.argv[1]
run(f"{RECREATE_COMMAND} {distro}")

print()
print("adding to known_hosts")
run(f"ssh-keyscan {TARGET_NAME} | tee ~/.ssh/known_hosts")

print("++++++++++++++++++++++++++++++++")
print("done")
print("++++++++++++++++++++++++++++++++")
