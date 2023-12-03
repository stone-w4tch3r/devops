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

enable_root_command = """pyinfra inventory.py --sudo exec -- 'echo "root:rnd_root_p4ss" | sudo chpasswd'"""

print("++++++++++++++++++++++++++++++++")
print("running simple tests")
print("++++++++++++++++++++++++++++++++")

print("deploy: basic, ubuntu")
run(f"scripts/recreate_target.py {ubuntu_distro}")
run(run_basic_complexity_normal)
run(run_basic_complexity_extended)

print("deploy: basic, debian")
run(f"scripts/recreate_target.py {debian_distro}")
run(run_basic_complexity_normal)
run(run_basic_complexity_extended)

print("deploy: rooted, ubuntu")
run(f"scripts/recreate_target.py {ubuntu_distro}")
run(run_rooted_complexity_normal)
run(run_rooted_complexity_extended)

print("deploy: rooted, debian")
run(enable_root_command)
run(f"scripts/recreate_target.py {debian_distro}")
run(run_rooted_complexity_normal)
run(run_rooted_complexity_extended)

print("++++++++++++++++++++++++++++++++")
print("tests passed")
print("++++++++++++++++++++++++++++++++")
