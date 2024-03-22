#!/usr/bin/env python3

import os
import subprocess

from multipass_vm_recreate import main as multipass_vm_recreate

TARGET_NAME = "primary.multipass"
DEFAULT_DISTRO = "jammy"


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


# todo: rewrite to ssh only script, not recreate_full
# todo: test both in-python and cli call
def main(distro: str = DEFAULT_DISTRO):
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
    distro = distro if len(os.sys.argv) <= 1 else os.sys.argv[1]
    multipass_vm_recreate(distro)

    print()
    print("adding to known_hosts")
    run(f"ssh-keyscan {TARGET_NAME} | tee ~/.ssh/known_hosts")

    print("++++++++++++++++++++++++++++++++")
    print("done")
    print("++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main()
