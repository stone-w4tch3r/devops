#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


def main(image: str = "jammy"):
    run("sudo echo '>>>This script restarts multipass instance and updates /etc/hosts'")

    run("multipass stop primary1", ignore_errs=True)
    run("multipass delete primary1", ignore_errs=True)
    run("multipass purge", ignore_errs=True)
    print(">>>multipass instances stopped and deleted")

    image = image if len(os.sys.argv) <= 1 else os.sys.argv[1]
    cloud_init_yml = Path(__file__).parent.resolve() / "multipass-vm-cloud-init.yml"
    print(cloud_init_yml)
    run(f"multipass launch -d 15G -n primary1 {image}")
    print(">>>multipass instance launched")

    primary_ip = subprocess.check_output("multipass list", shell=True, universal_newlines=True).split("\n")[1].split()[2]
    print(f"Primary IP: {primary_ip}")
    print(">>>done")


if __name__ == "__main__":
    main()
