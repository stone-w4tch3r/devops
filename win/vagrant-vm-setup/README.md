# Windows Development VM Setup

Simple windows dev vm with basic configuration

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
   - Auto resolve required provider (virtualbox/parallels)
   - Download windows 11 image
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

## Running Ansible Standalone

If you want to run the Ansible playbook separately from Vagrant (for example, to reconfigure an existing VM or troubleshoot specific roles), follow these steps:

1. **Create an inventory file**:

   Create a file named `inventory.ini` in the ansible directory:

   ```ini
   [windows]
   windev ansible_host=IP_ADDRESS_OF_YOUR_VM

   [windows:vars]
   ansible_user=vagrant
   ansible_password=vagrant
   ansible_connection=winrm
   ansible_winrm_transport=basic
   ansible_winrm_server_cert_validation=ignore
   ```

   Replace `IP_ADDRESS_OF_YOUR_VM` with the actual IP address of your Windows VM.

2. **Run the Ansible playbook manually**:

   ```bash
   cd /path/to/devops/win/vagrant-vm-setup
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
   ```

3. **Run specific tags only**:

   ```bash
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags "winget_packages,powershell"
   ```

4. **Skip specific roles**:

   ```bash
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --skip-tags "vbox_guestadditions"
   ```

5. **Pass variables via CLI**:

   ```bash
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml -e "is_vbox=true"
   ```

## Troubleshooting

### Vagrant Issues

- If you encounter WinRM connection errors, try running `vagrant reload` to restart the VM

### Ansible Issues

- If Ansible provisioning fails, you can retry with `vagrant provision`
- Check the Ansible logs for detailed error information
