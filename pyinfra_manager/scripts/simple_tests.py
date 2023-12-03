#!/usr/bin/env python3
import os
import subprocess


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


ubuntu_distro = "jammy"
debian_distro = "file:///home/user1/VMs/debian-12-generic-amd64.qcow2"

run_basic_complexity_normal = ("pyinfra inventory.py playbooks/all.py "
                               + "--data aliases_complexity=Normal "
                               + "--data zsh_complexity=Normal "
                               + "--data tools_complexity=Normal")
run_basic_complexity_extended = ("pyinfra inventory.py playbooks/all.py "
                                 + "--data aliases_complexity=Extended "
                                 + "--data zsh_complexity=Extended "
                                 + "--data tools_complexity=Extended")
run_rooted_complexity_normal = ("pyinfra inventory.py playbooks/all.py "
                                + "--ssh-user root --ssh-password rnd_root_p4ss "
                                + "--data aliases_complexity=Normal "
                                + "--data zsh_complexity=Normal "
                                + "--data tools_complexity=Normal")
run_rooted_complexity_extended = ("pyinfra inventory.py playbooks/all.py "
                                  + "--ssh-user root --ssh-password rnd_root_p4ss "
                                  + "--data aliases_complexity=Extended "
                                  + "--data zsh_complexity=Extended "
                                  + "--data tools_complexity=Extended")
enable_root_command = ("pyinfra inventory.py --sudo exec -- "
                       + "'"
                       + 'echo "root:rnd_root_p4ss" | sudo chpasswd '
                       + '&& echo "PermitRootLogin yes" | sudo tee /etc/ssh/sshd_config.d/90-enable-root-login.conf '
                       + "&& sudo systemctl reload sshd"
                       + "'")
test_command = "pyinfra inventory.py --sudo exec -- 'sudo echo test'"

tests_to_run = [1, 2, 3, 4]
if os.sys.argv[1:]:
    tests_to_run = [int(arg) for arg in os.sys.argv[1:]]

print("##########################################")
print(f"running simple tests: {tests_to_run}")
print("##########################################")

if 1 in tests_to_run:
    print("deploy: basic, ubuntu\n")
    run(f"scripts/recreate_target.py {ubuntu_distro}")
    run(run_basic_complexity_normal)
    run(run_basic_complexity_extended)

if 2 in tests_to_run:
    print("deploy: basic, debian\n")
    run(f"scripts/recreate_target.py {debian_distro}")
    run(run_basic_complexity_normal)
    run(run_basic_complexity_extended)

if 3 in tests_to_run:
    print("deploy: rooted, ubuntu\n")
    run(f"scripts/recreate_target.py {ubuntu_distro}")
    run(enable_root_command)
    run(run_rooted_complexity_normal)
    run(test_command)

if 4 in tests_to_run:
    print("deploy: rooted, debian\n")
    run(f"scripts/recreate_target.py {debian_distro}")
    run(enable_root_command)
    run(run_rooted_complexity_normal)
    run(test_command)

print("##########################################")
print(f"tests passed: {tests_to_run}")
print("##########################################")
