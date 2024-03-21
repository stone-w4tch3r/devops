#!/bin/bash

OVA_FILE="$HOME/VMs/jammy-server-cloudimg-amd64.ova"
SEED_ISO="./ubuntu-seed.iso"
CLOUD_INIT="./ubuntu-cloud-init.yml"
VM_NAME="UbuntuVM"
CPU_COUNT=2
RAM_IN_MB=2048

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Welcome to the VM starter script"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo -e "\n"

if VBoxManage list vms | grep -q "$VM_NAME"; then
    echo "VM already exists. Deleting it..."
    VBoxManage controlvm "$VM_NAME" poweroff
    VBoxManage unregistervm "$VM_NAME" --delete
    echo "VM deleted"
fi

cloud-localds "$SEED_ISO" "$CLOUD_INIT"
VBoxManage import "$OVA_FILE" --vsys 0 --vmname "$VM_NAME"
VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium "$SEED_ISO"
VBoxManage modifyvm "$VM_NAME" --cpus "$CPU_COUNT" --memory "$RAM_IN_MB"
VBoxManage startvm "$VM_NAME" --type headless
info=$(VBoxManage showvminfo "$VM_NAME")

sleep 45

echo -e "\n"
echo "VM started"
echo "VM Name: $(echo "$info" | grep "Name:" | awk '{print $2}')"
echo "VM State: $(echo "$info" | grep "State:" | awk '{print $2}')"
echo "VM OS: $(echo "$info" | grep "Guest OS:" | awk '{print $3}')"
echo "VM IP: $(VBoxManage guestproperty get UbuntuVM "/VirtualBox/GuestInfo/Net/0/V4/IP" | awk '{print $2}')"

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Done"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"