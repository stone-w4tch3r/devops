#!/usr/bin/env python3

import subprocess, os
from pathlib import Path


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


run("multipass stop primary1", ignore_errs=True)
run("multipass delete primary1", ignore_errs=True)
run("multipass purge", ignore_errs=True)
print(">>>multipass instances stopped and deleted")

image = "jammy" if len(os.sys.argv) <= 1 else os.sys.argv[1]
script_path = Path(__file__).parent.resolve()
run(f"multipass launch -d 15G -n primary1 --cloud-init {script_path}/vm-cloud-init.yml {image}")
run(f"ssh-keygen -f /home/{os.getlogin()}/.ssh/known_hosts -R primary.multipass")
print(">>>multipass instance launched")

primary_ip = subprocess.check_output("multipass list", shell=True, universal_newlines=True).split("\n")[1].split()[2]

run(f'sudo sed -i "s|.*primary.*|{primary_ip} primary.multipass|g" /etc/hosts')
print(">>>done")
