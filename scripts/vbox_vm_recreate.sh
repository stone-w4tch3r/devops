#!/bin/bash
set -euo pipefail

TMPDIR=${TMPDIR:-/tmp}

ova_file="$HOME/VMs/jammy-server-cloudimg-amd64.ova"
seed_iso="$TMPDIR/ubuntu-seed.iso"
cloud_init="./vbox-vm-cloud-init.yml"
vm_name="vbox-primary"
cpu_count=2
ram_in_mb=2048

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Welcome to the VM starter script"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
sudo echo ""

if VBoxManage list vms | grep -q "$vm_name"; then
    echo "VM already exists. Deleting it..."
    VBoxManage controlvm "$vm_name" poweroff
    VBoxManage unregistervm "$vm_name" --delete
    echo "VM deleted"
fi

echo "Creating VM..."
cloud-localds "$seed_iso" "$cloud_init"
VBoxManage import "$ova_file" --vsys 0 --vmname "$vm_name"
VBoxManage storageattach "$vm_name" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$seed_iso"
VBoxManage modifyvm "$vm_name" --cpus "$cpu_count" --memory "$ram_in_mb"
VBoxManage startvm "$vm_name" --type headless

sleep 45

info=$(VBoxManage showvminfo "$vm_name")
vm_state=$(echo "$info" | grep "State:" | awk '{print $2}')
vm_os=$(echo "$info" | grep "Guest OS:" | awk '{print $3}')
vm_ip=$(VBoxManage guestproperty get "$vm_name" "/VirtualBox/GuestInfo/Net/0/V4/IP" | awk '{print $2}')


echo -e "\n"
echo "VM started"
echo "VM Name: $vm_name"
echo "VM State: $vm_state"
echo "VM OS: $vm_os"


function is_vm_ip_valid() {
  if [[ "$vm_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then  #[[ ]] means regex, =~ means match
    return 0
  else
    return 1
  fi
}

if ! is_vm_ip_valid; then
    sleep 10
    vm_ip=$(VBoxManage guestproperty get "$vm_name" "/VirtualBox/GuestInfo/Net/0/V4/IP" | awk '{print $2}')
    
    if ! is_vm_ip_valid; then
        echo "VM IP not found. Try it yourself"
        exit 1
    fi
fi
echo "VM IP: $vm_ip"

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Done"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"