# Windows Development VM Setup

This project provides an automated setup for a Windows 10 development virtual machine using Vagrant and Ansible. It's designed to work cross-platform, allowing you to create consistent Windows development environments on macOS, Linux, or Windows hosts.

## Prerequisites

### For macOS

1. **Install VirtualBox, Vagrant, and Ansible**:

   ```bash
   brew install --cask virtualbox
   brew install --cask vagrant
   brew install ansible
   ```

2. **Install Parallels somehow**

3. **Prepare vagrant for Parallels**:

   ```bash
   vagrant plugin install vagrant-parallels
   ```

### For Linux (Ubuntu/Debian)

1. **Install VirtualBox, Vagrant, and Ansible**:

   ```bash
   sudo apt update
   sudo apt install virtualbox -y
   sudo apt install ansible -y
   ```

2. **Install Vagrant**:

   ```bash
   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
   sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
   sudo apt update
   sudo apt install vagrant
   ```

### For Linux (Fedora/RHEL/CentOS)

1. **Install VirtualBox**:

   Preinstall RPMFusion repository, [read more](https://rpmfusion.org/Howto/VirtualBox)

   ```bash
   dnf install VirtualBox
   akmods
   systemctl restart vboxdrv
   lsmod  | grep -i vbox
   ```

2. **Install Vagrant and Ansible**:

   ```bash
   sudo dnf install vagrant
   sudo dnf install ansible
   ```

## Setup Instructions

1. **Clone this repository** (if you haven't already)

2. **Navigate to the vagrant-vm-setup directory**:

   ```bash
   cd /path/to/devops/win/vagrant-vm-setup
   ```

3. **Start the VM**:

   ```bash
   vagrant up
   ```

   This will:
   - Download the Windows 10 box
   - Create and configure the VM
   - Run the Ansible playbook to set up the development environment

4. **Access the VM**:
   - The VM will start with a GUI
   - Login with username: `vagrant` and password: `vagrant`

5. **Manage the VM**:
   - **Suspend the VM**: `vagrant suspend`
   - **Resume the VM**: `vagrant resume`
   - **Stop the VM**: `vagrant halt`
   - **Delete the VM**: `vagrant destroy`

## Troubleshooting

### Vagrant Issues

- If you encounter WinRM connection errors, try running `vagrant reload` to restart the VM

### Ansible Issues

- If Ansible provisioning fails, you can retry with `vagrant provision`
- Check the Ansible logs for detailed error information
