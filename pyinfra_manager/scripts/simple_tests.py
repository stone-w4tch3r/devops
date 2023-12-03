import subprocess


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


first_distro = "jammy"
second_distro = "file:///home/user1/VMs/debian-12-generic-amd64.qcow2"

first_run = ("pyinfra inventory.py playbooks/all.py "
             + "--data aliases_complexity=Normal "
             + "--data zsh_complexity=Normal "
             + "--data tools_complexity=Normal")
second_run = ("pyinfra inventory.py playbooks/all.py "
              + "--data aliases_complexity=Extended "
              + "--data zsh_complexity=Extended "
              + "--data tools_complexity=Extended")
third_run = ("pyinfra inventory.py playbooks/all.py "
             + "--ssh-user root --ssh-password rnd_root_p4ss "
             + "--data aliases_complexity=Normal "
             + "--data zsh_complexity=Normal "
             + "--data tools_complexity=Normal")
fourth_run = ("pyinfra inventory.py playbooks/all.py "
              + "--ssh-user root --ssh-password rnd_root_p4ss "
              + "--data aliases_complexity=Extended "
              + "--data zsh_complexity=Extended "
              + "--data tools_complexity=Extended")

print("++++++++++++++++++++++++++++++++")
print("running simple tests")
print("++++++++++++++++++++++++++++++++")

print("first deploy")
run(f"scripts/recreate_target.py {first_distro}")
run(first_run)
run(second_run)

print("second deploy")
run(f"scripts/recreate_target.py {second_distro}")
run(first_run)
run(second_run)

print("third deploy")
run(f"scripts/recreate_target.py {first_distro}")
run(third_run)
run(fourth_run)

print("fourth deploy")
run(f"scripts/recreate_target.py {second_distro}")
run(third_run)
run(fourth_run)

print("++++++++++++++++++++++++++++++++")
print("tests passed")
print("++++++++++++++++++++++++++++++++")
