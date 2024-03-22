#!/usr/bin/env pwsh

function Get-IsIpValid {
    param($vm_ip)
    return ($vm_ip -match "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
}

function Get-VmIp {
    param($vm_name)
    return VBoxManage guestproperty get $vm_name "/VirtualBox/GuestInfo/Net/0/V4/IP" | Select-String "Value:" | ForEach-Object { ($_.Line -split '\s+')[1] }
}

$TMPDIR = $null -ne $env:TMPDIR ? $env:TMPDIR : "/tmp"

$ova_file = "$HOME/VMs/jammy-server-cloudimg-amd64.ova"
$seed_iso = "$TMPDIR/ubuntu-seed.iso"
$cloud_init = "./vbox-vm-cloud-init.yml"
$vm_name = "vbox-primary"
$cpu_count = 2
$ram_in_mb = 2048

Write-Host ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
Write-Host "Welcome to the VM starter script"
Write-Host ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

if ((VBoxManage list vms) -match $vm_name) {
    Write-Host "VM already exists. Deleting it..."
    VBoxManage controlvm $vm_name poweroff
    VBoxManage unregistervm $vm_name --delete
    Write-Host "VM deleted"
}

Write-Host "Creating VM..."
cloud-localds $seed_iso $cloud_init
VBoxManage import $ova_file --vsys 0 --vmname $vm_name
VBoxManage storageattach $vm_name --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium $seed_iso
VBoxManage modifyvm $vm_name --cpus $cpu_count --memory $ram_in_mb
VBoxManage startvm $vm_name --type headless

Start-Sleep -s 45

$info = VBoxManage showvminfo $vm_name
$vm_state = $info | Select-String "State:" | ForEach-Object { ($_.Line -split '\s+')[1] }
$vm_os = $info | Select-String "Guest OS:" | ForEach-Object { ($_.Line -split '\s+')[2..3] }
$vm_ip = Get-VmIp $vm_name

Write-Host ""
Write-Host "VM started"
Write-Host "VM Name: $vm_name"
Write-Host "VM State: $vm_state"
Write-Host "VM OS: $vm_os"

if (!(Get-IsIpValid $vm_ip)) {
    Start-Sleep -s 10
    $vm_ip = Get-VmIp $vm_name

    if (!(Get-IsIpValid $vm_ip)) {
        Write-Host "VM IP not found. Try it yourself"
        exit 1
    }
}
Write-Host "VM IP: $vm_ip"

Write-Host ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
Write-Host "Done"
Write-Host ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"