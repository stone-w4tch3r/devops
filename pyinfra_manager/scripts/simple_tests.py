import subprocess


def run(cmd: str, ignore_errs: bool = False):
    return subprocess.run(cmd, shell=True, check=not ignore_errs)


first_distro = "jammy"
second_distro = "focal"
third_distro = "file:///home/user1/VMs/debian-12-generic-amd64.qcow2"

print("++++++++++++++++++++++++++++++++")
print("running simple tests")
print("++++++++++++++++++++++++++++++++")

print("first deploy")
run(f"scripts/recreate_target.py {first_distro}")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Basic")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Extended")

print("second deploy")
run(f"scripts/recreate_target.py {second_distro}")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Basic")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Extended")

print("third deploy")
run(f"scripts/recreate_target.py {third_distro}")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Basic")
run("pyinfra inventory.py all_deploys.py --data instance_complexity=Extended")

