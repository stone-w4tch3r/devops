#!/bin/bash
set -euo pipefail

TMPDIR=${TMPDIR:-/tmp}
OVA_FILE="$HOME/VMs/jammy-server-cloudimg-amd64.ova"
SEED_ISO="$TMPDIR/ubuntu-seed.iso"
CLOUD_INIT="./vbox-vm-cloud-init.yml"
VM_NAME="vbox-primary"
CPU_COUNT=2
RAM_IN_MB=2048

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Welcome to the VM starter script"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
sudo echo ""

if VBoxManage list vms | grep -q "$VM_NAME"; then
    echo "VM already exists. Deleting it..."
    VBoxManage controlvm "$VM_NAME" poweroff
    VBoxManage unregistervm "$VM_NAME" --delete
    echo "VM deleted"
fi

echo "Creating VM..."
cloud-localds "$SEED_ISO" "$CLOUD_INIT"
VBoxManage import "$OVA_FILE" --vsys 0 --vmname "$VM_NAME"
VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$SEED_ISO"
VBoxManage modifyvm "$VM_NAME" --cpus "$CPU_COUNT" --memory "$RAM_IN_MB"
VBoxManage startvm "$VM_NAME" --type headless

sleep 45

info=$(VBoxManage showvminfo "$VM_NAME")
vm_state=$(echo "$info" | grep "State:" | awk '{print $2}')
vm_os=$(echo "$info" | grep "Guest OS:" | awk '{print $3}')
vm_ip=$(VBoxManage guestproperty get "$VM_NAME" "/VirtualBox/GuestInfo/Net/0/V4/IP" | awk '{print $2}')


echo -e "\n"
echo "VM started"
echo "VM Name: $VM_NAME"
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
    vm_ip=$(VBoxManage guestproperty get "$VM_NAME" "/VirtualBox/GuestInfo/Net/0/V4/IP" | awk '{print $2}')
    
    if ! is_vm_ip_valid; then
        echo "VM IP not found. Try it yourself"
        exit 1
    fi
fi
echo "VM IP: $vm_ip"

ssh-keygen -f "$HOME/.ssh/known_host" -R "$vm_ip" > /dev/null 2>&1  #2>&1 - redirect stderr to stdout
ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$VM_NAME" > /dev/null 2>&1

sudo sed -i "|$VM_NAME|d" /etc/hosts  #|PATTERN|d - delete line with PATTERN
echo "$vm_ip $VM_NAME" | sudo tee -a /etc/hosts > /dev/null

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Done"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"