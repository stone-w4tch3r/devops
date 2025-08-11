Process, from .

## Run new VM from a template via virt manager

```bash
# Step 0: Install cloud config tools (in distrobox)
sudo dnf install -y cloud-utils

# Step 1: prepare seed.iso for cloud-init (in distrobox)
cp meta-data-devbox.yml meta-data-devbox.local.yml
sed -i 's/devbox-n/devbox-0/' meta-data-devbox.local.yml
cloud-localds seed.local.iso cloud-config-devbox.yml meta-data-devbox.local.yml

# Step 2: mount seed in virt manager
# ...
```

## Template VM Creation via quickemu (recommended)

```bash
# Step 1: Create clean base image (do this once)
wget -O ubuntu-24.04-master.qcow2 https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
chmod 444 ubuntu-24.04-master.qcow2  # make read-only

# Step 2: Install cloud config tools (in distrobox)
sudo dnf install -y cloud-utils

# Step 3: Create cloud-init seed (in distrobox)
cloud-localds seed.iso cloud-config-ubuntu-golden.yml meta-data-ubuntu-golden.yml

# Step 4: Prepare image
cp ubuntu-24.04-master.qcow2 ubuntu-24.04-golden.qcow2
chmod a+rwx ubuntu-24.04-golden.qcow2
qemu-img resize ubuntu-24.04-golden.qcow2 16G

# Step 5: start VM
mkdir ubuntu-quickemu/
cp ubuntu-quickemu.conf seed.iso ubuntu-quickemu/
mv ubuntu-24.04-golden.qcow2 ubuntu-quickemu/
cd ubuntu-quickemu/
quickemu --vm ubuntu-quickemu.conf --display spice

# Step 6: wait for provisioning to finish
# check live via `sudo cloud-init status --long`
# and monitor /var/log/cloud-init-output.log

# Step 7: save VM as a template
sudo cloud-init clean # in VM

sudo virt-sysprep -a ubuntu-24.04-golden.qcow2 --operations machine-id,udev-persistent-net,logfiles # remove some state
chmod 444 ubuntu-24.04-golden.qcow2 # make read-only
cp ubuntu-24.04-golden.qcow2 ~/VMs
```

## Template VM Creation via libvirt

```bash
# Step 1: Create clean base image (do this once)
wget -O ubuntu-24.04-master.qcow2 https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
chmod 444 ubuntu-24.04-master.qcow2  # make read-only

# Step 2: Install cloud config tools (in distrobox)
sudo dnf install -y cloud-utils

# Step 3: Create cloud-init seed (in distrobox)
cloud-localds seed.iso cloud-config-ubuntu-golden.yml meta-data-ubuntu-golden.yml

# Step 4: Prepare image
cp ubuntu-24.04-master.qcow2 ubuntu-24.04-golden.qcow2
chmod a+rwx ubuntu-24.04-golden.qcow2
qemu-img resize ubuntu-24.04-golden.qcow2 16G

# Step 5: Create template VM
virt-install --connect qemu:///system \
  --name devbox-gold \
  --memory 4096 --vcpus 2 \
  --disk path=$PWD/ubuntu-24.04-golden.qcow2,format=qcow2,bus=virtio \
  --disk path=$PWD/seed.iso,device=cdrom \
  --os-variant ubuntu24.04 \
  --graphics spice \
  --network network=default,model=virtio \
  --import

# Step 6: wait for provisioning to finish
# check live via `sudo cloud-init status --long`
# and monitor /var/log/cloud-init-output.log

# Step 7: Create additional VMs (fast clones)
qemu-img create -f qcow2 -F qcow2 -b ubuntu-24.04-golden.qcow2 project1.qcow2
virt-install --connect qemu:///system --name project1 --memory 4096 --vcpus 2 \
  --disk path=$PWD/project1.qcow2,format=qcow2,bus=virtio \
  --disk path=$PWD/seed.iso,device=cdrom \
  --os-variant ubuntu24.04 --graphics spice \
  --network network=default,model=virtio --import
```

## Setup virt-manager without sudo

```bash
# Create a group


# Add user to libvirt group
sudo usermod -a -G libvirt $USER

# Enable and start libvirt services
sudo systemctl enable --now libvirtd
sudo systemctl enable --now virtlogd

# You need to log out and back in for group changes to take effect
# Then you can use virt-manager without sudo and connect to qemu:///system

# Alternative: you can also use newgrp to activate the group in current session
# newgrp libvirt

# Verify access without sudo:
# virsh list --all                           # connects to user session
# virsh --connect qemu:///system list --all  # connects to system-wide VMs
# virt-manager (should connect to qemu:///system automatically)

# Note: VMs created with 'sudo virt-install' go to system connection
# VMs created with regular 'virt-install' go to user session connection

# IMPORTANT: User-level libvirt has networking issues!
# User sessions don't have default networks and need complex setup for networking
# Recommendation: Use system connection (qemu:///system) for VMs that need networking
```

## qcow2 Image Management

**Why redownload?** VMs write directly to qcow2 files, making them "dirty" with:
- Installed packages, user accounts, logs
- Partition changes (cloud-init resizing)
- Runtime state, caches, temp files

**Better alternatives:**

### Option 1: Keep a clean master image

```bash
# Download once, keep as read-only master
wget -O ubuntu-24.04-master.qcow2 https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
qemu-img resize ubuntu-24.04-master.qcow2 16G
chmod 444 ubuntu-24.04-master.qcow2  # make read-only

# Copy for each VM
cp ubuntu-24.04-master.qcow2 ubuntu-24.04-vm1.qcow2
```

### Option 2: Use qcow2 backing files (recommended)

```bash
# Create clean master (backing file)
wget -O ubuntu-24.04-master.qcow2 https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
qemu-img resize ubuntu-24.04-master.qcow2 16G

# Create overlay images (only store differences)
qemu-img create -f qcow2 -F qcow2 -b ubuntu-24.04-master.qcow2 vm1.qcow2
qemu-img create -f qcow2 -F qcow2 -b ubuntu-24.04-master.qcow2 vm2.qcow2

# Benefits: Fast VM creation, space-efficient (overlays ~100MB vs 16GB copies)
# Considerations: Don't delete/move the base file while VMs are using it
```
