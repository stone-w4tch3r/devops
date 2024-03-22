import os
import re
import subprocess
import time


def run(command) -> str:
    return subprocess.check_output(command, shell=True).decode().strip()


def is_ip_valid(ip) -> bool:
    return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip))


TMPDIR = os.getenv('TMPDIR', '/tmp')

ova_file = os.path.join(os.getenv('HOME'), "VMs/jammy-server-cloudimg-amd64.ova")
seed_iso = os.path.join(TMPDIR, "ubuntu-seed.iso")
cloud_init = "./vbox-vm-cloud-init.yml"
vm_name = "vbox-primary"
cpu_count = 2
ram_in_mb = 2048

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
vm_ip = run(f"VBoxManage guestproperty get {vm_name} '/VirtualBox/GuestInfo/Net/0/V4/IP'").split()[-1]

print("\n")
print("VM started")
print(f"VM Name: {vm_name}")
print(f"VM State: {vm_state}")
print(f"VM OS: {vm_os}")

if not is_ip_valid(vm_ip):
    time.sleep(10)
    vm_ip = run(f"VBoxManage guestproperty get {vm_name} '/VirtualBox/GuestInfo/Net/0/V4/IP'").split()[-1]

    if not is_ip_valid(vm_ip):
        print("VM IP not found. Try it yourself")
        exit(1)

print(f"VM IP: {vm_ip}")

print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print("Done")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
